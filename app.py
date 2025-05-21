from flask import Flask, request, send_file, redirect, url_for, render_template, session ,jsonify
import pandas as pd
import os
from tempfile import NamedTemporaryFile
import multiprocessing
from tkinter import filedialog, Tk
import cv2
import numpy as np
import uuid
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import url_for
from flask_cors import CORS
import subprocess
import ffmpeg
import json
import copy
from flask import Response


app = Flask(__name__)
app.secret_key = (
    "test_123"  # Must be set for using session #dummy string used
)
CORS(app)  # Enable Cross-Origin Resource Sharing

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["PROCESSED_FOLDER"] = os.path.join("static", "processed")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROCESSED_FOLDER"], exist_ok=True)

upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)  
TEMP_DATA = {}


class ForegroundDetector:
    def __init__(
        self,
        num_gaussians,
        min_background_ratio,
        initial_variance,
        learning_rate,
        num_training_frames=500,
        adapt_learning_rate=True,
    ):
        self.num_gaussians = num_gaussians
        self.min_background_ratio = min_background_ratio
        self.initial_variance = initial_variance
        self.adapt_learning_rate = adapt_learning_rate
        self.num_training_frames = num_training_frames
        self.learning_rate = learning_rate
        self.time = 0
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=num_training_frames, detectShadows=False
        )
        self.bg_subtractor.setBackgroundRatio(min_background_ratio)
        self.bg_subtractor.setNMixtures(num_gaussians)
        self.bg_subtractor.setHistory(num_training_frames)
        self.bg_subtractor.setVarInit(initial_variance)
        self.initialized = True

    def initialize(self, frame):
        self.initialized = True

    def step(self, frame, learning_rate=None):
        if not self.initialized:
            self.initialize(frame)

        self.time += 1
        # Apply the background subtractor
        fg_mask = self.bg_subtractor.apply(frame, learningRate=learning_rate)
        return fg_mask

    def reset(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self.num_training_frames, detectShadows=False
        )
        self.bg_subtractor.setBackgroundRatio(self.min_background_ratio)
        self.bg_subtractor.setNMixtures(self.num_gaussians)
        self.time = 0

def optimize_mp4_for_browser(input_path):
    """
    Optimizes an MP4 file for browser playback (Fast Start) by overwriting the original file.
    """
    import os
    import subprocess

    temp_path = input_path.replace(".mp4", "_temp.mp4")

    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-movflags",
        "faststart",
        "-c",
        "copy",
        temp_path,
    ]

    try:
        subprocess.run(cmd, check=True)
        os.replace(temp_path, input_path)  # Overwrite original with optimized version
        return input_path
    except subprocess.CalledProcessError as e:
        return input_path


def process_video(input_video_path, output_video_path, params):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        return

    # Create a ForegroundDetector instance using the provided parameters
    detector = ForegroundDetector(**params)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    twitch_time_sec = 0.2  # 200 milliseconds
    window_size = int(fps * twitch_time_sec)

    # Use MP4 codec
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Blob detector
    A = np.array([width, height])
    pcent = np.round((A / 10) * (10 / 10))  # minBlob=10 default
    sz = int(np.round(np.sqrt(pcent[0] * pcent[1])))

    params_blob = cv2.SimpleBlobDetector_Params()
    params_blob.filterByArea = True
    params_blob.minArea = sz
    params_blob.filterByCircularity = False
    params_blob.filterByConvexity = False
    params_blob.filterByInertia = False
    blob_detector = cv2.SimpleBlobDetector_create(params_blob)

    frame_count = 0
    window_frame_counter = 0
    blob_found_in_window = False
    prev_frame_blob_found = (
        False  # To track if blobs were detected in the previous frame
    )
    prev_window_had_blob = False
    fasciculation_count = 0
    all_keypoints = []  # To collect all keypoints

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        fg_mask = detector.step(frame)

        if frame_count > 500:
            keypoints = blob_detector.detect(fg_mask)

            # Initialize current_frame_blob_found to False
            current_frame_blob_found = False

            # Detect blobs in the current frame
            if len(keypoints) > 4:
                current_frame_blob_found = (
                    True  # More than one blob in the current frame
                )

            # Only consider the blobs as found if blobs were detected in both the current and the previous frame
            if current_frame_blob_found and prev_frame_blob_found:
                blob_found_in_window = True  # Blobs detected in consecutive frames

            # Visual overlays (if required)
            centroids = []
            for k in keypoints:
                x, y = int(k.pt[0]), int(k.pt[1])
                centroids.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Red dot

            all_keypoints.append(centroids)

            # Connect blobs with lines (one line for each pair)
            for i in range(len(centroids) - 1):  # Ensure we don't go out of bounds
                pt1 = centroids[i]
                pt2 = centroids[i + 1]  # Connect blob i to blob i+1
                cv2.line(frame, pt1, pt2, (255, 255, 0), 1)  # Cyan line

            # Update previous frame blob found state for the next iteration
            prev_frame_blob_found = current_frame_blob_found

        # End of twitch window — check for fasciculation
        if window_frame_counter >= window_size:
            if blob_found_in_window and not prev_window_had_blob:
                fasciculation_count += 1
                prev_window_had_blob = True
            elif not blob_found_in_window:
                prev_window_had_blob = False

            # Reset for next window
            blob_found_in_window = False
            window_frame_counter = 0

        out.write(frame)

        frame_count += 1
        window_frame_counter += 1

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    output_video_path = optimize_mp4_for_browser(output_video_path)

    return jsonify({
        'fasciculation_count': fasciculation_count,
        'all_keypoints': all_keypoints,
        'fps': fps
    }), 200

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return "No video file provided", 400

    video = request.files["video"]
    muscle_group = request.form.get("muscle_group")
    probe_orientation = request.form.get("probe_orientation")

    filename = secure_filename(video.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    unique_id = str(uuid.uuid4())
    base, ext = os.path.splitext(filename)
    saved_name = f"{base}_{unique_id}{ext}"
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
    video.save(input_path)

    output_filename = f"processed_{unique_id}.mp4"  # not .avi
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)

    # Define parameter map
    param_map = {
        ("BB", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("BB", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.80,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("MG", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("MG", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TRAP", "transverse"): {
            "num_gaussians": 4,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TRAP", "longitudinal"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.5,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("RA", "transverse"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("RA", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TP", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.005,
            "num_training_frames": 100,
            "adapt_learning_rate": True,
        },
        ("TP", "longitudinal"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.005,
            "num_training_frames": 300,
            "adapt_learning_rate": True,
        },
    }

    params = param_map.get(
        (muscle_group, probe_orientation),
        {
            "num_gaussians": 5,
            "min_background_ratio": 0.7,
            "initial_variance": 30 * 30,
            "learning_rate": 0.01,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
    )

    result = process_video(input_path, output_path, params)
    response = result[0]  #Flask Response object

    if isinstance(response, Response):
        json_data = response.get_json()

        fasciculation_count = json_data.get('fasciculation_count')
        all_keypoints = json_data.get('all_keypoints')
        fps = json_data.get('fps')

    else:
        print(">> Not a Flask Response object:", response)

    # Redirect to the result page
    return redirect(url_for("result",
                        processed=output_filename,
                        count=fasciculation_count,
                        keypoints=json.dumps(all_keypoints),
                        original=filename,
                        muscle=muscle_group,
                        probe=probe_orientation,
                        fps=fps))

@app.route("/<path:filename>")
def serve_video(filename):
    return send_from_directory("processed", filename)

@app.route("/result")
def result():
    processed_video = request.args.get("processed")
    fasciculation_count = request.args.get("count", 0)
    all_keypoints_json = request.args.get("keypoints", "[]")
    filename_1 = request.args.get("original")
    muscle_group = request.args.get("muscle")
    probe_orientation = request.args.get("probe")
    fps = request.args.get("fps")

    # Deserialize all_keypoints from JSON
    all_keypoints = json.loads(all_keypoints_json)

    if processed_video is None:
        return redirect(url_for("index"))

    # Convert the filename into a valid video URL
    video_url = url_for("serve_video", filename=processed_video)

      # Muscle group mapping
    muscle_group_map = {
        'BB': 'Biceps Brachii',
        'MG': 'Medial Gastrocnemius',
        'TP': 'Thoracic Paraspinal',
        'ADM': 'Abductor Digiti Minimi',
        'TRAP': 'Trapezius',
        'RA': 'Rectus Abdominis'
    }
    muscle_group_label = muscle_group_map.get(muscle_group, muscle_group) 

    return render_template(
        "result.html",
        video_url=video_url,
        fasciculation_count=fasciculation_count,
        keypoints=all_keypoints,
        filename=filename_1,
        muscle_group=muscle_group_label,
        probe_orientation=probe_orientation,
        fps=fps
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download_template", methods=["GET"])
def download_template():
    try:
        columns = ["trial_name", "muscle_group", "probe_orientation", "file_path"]
        df = pd.DataFrame(columns=columns)
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            template_path = temp_file.name
            df.to_excel(template_path, index=False)
        return send_file(
            template_path,
            as_attachment=True,
            download_name="video_upload_template.xlsx",
        )

    except Exception as e:
        return "Error generating Excel file", 500

    finally:
        # Clean up the temporary file after sending it
        if os.path.exists(template_path):
            os.remove(template_path)


def select_folder_gui():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path


@app.route("/select-folder", methods=["POST"])
def select_folder():
    # Run Tkinter folder selection in a separate process
    with multiprocessing.Pool(1) as pool:
        folder_path = pool.apply(select_folder_gui)

    if not folder_path:
        return jsonify({"success": False, "message": "No folder selected"})

    files = os.listdir(folder_path)  # Get all file names
    file_paths = [os.path.join(folder_path, file) for file in files]

    # Save to Excel
    df = pd.DataFrame(
        {
            "File Name": files,
            "Full_Path": file_paths,
            "muscle_group": ["" for _ in files],
            "probe_orientation": ["" for _ in files],
        }
    )

    output_file = os.path.join(folder_path, "files_list.xlsx")
    df.to_excel(output_file, index=False)

    return jsonify({"success": True, "file_url": f"/download-excel?path={output_file}"})


@app.route("/download-excel")
def download_excel():
    file_path = request.args.get("path")
    return send_file(file_path, as_attachment=True)


@app.route("/upload-excel", methods=["POST"])
def upload_excel():
    file = request.files["file"]
    if not file:
        return jsonify({"success": False, "message": "No file uploaded"})

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Read Excel or CSV
    if filename.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    param_map = {
        ("BB", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("BB", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.80,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("MG", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("MG", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TRAP", "transverse"): {
            "num_gaussians": 4,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TRAP", "longitudinal"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.5,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("RA", "transverse"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("RA", "longitudinal"): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True,
        },
        ("TP", "transverse"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.005,
            "num_training_frames": 100,
            "adapt_learning_rate": True,
        },
        ("TP", "longitudinal"): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 30,
            "learning_rate": 0.005,
            "num_training_frames": 300,
            "adapt_learning_rate": True,
        },
    }

    # Create a unique subfolder for this upload in static
    base_name = os.path.splitext(filename)[0]
    subfolder_path = os.path.join("static", "processed_videos", base_name)
    os.makedirs(subfolder_path, exist_ok=True)

    processed_videos = []

    # Process each row in Excel
    for idx, row in df.iterrows():
        try:
            video_path = row["Full_Path"]
            muscle_group = row["muscle_group"]
            probe_orientation = row["probe_orientation"]
            # Check for missing values (None or NaN)
            if pd.isna(video_path) or pd.isna(muscle_group) or pd.isna(probe_orientation):
                raise ValueError(
                    f"Missing data in row {idx}: "
                    f"Full_Path={video_path}, muscle_group={muscle_group}, probe_orientation={probe_orientation}"
                )

            output_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_processed.mp4"
            output_path = os.path.join(subfolder_path, output_name)
            params = param_map.get(
                (muscle_group, probe_orientation),
                {
                    "num_gaussians": 5,
                    "min_background_ratio": 0.7,
                    "initial_variance": 30 * 30,
                    "learning_rate": 0.01,
                    "num_training_frames": 500,
                    "adapt_learning_rate": True,
                },
            )

            result_bulk = process_video(video_path, output_path, params)
            response_bulk = result_bulk[0]  #Flask Response object

            if isinstance(response_bulk, Response):
                    json_data = response_bulk.get_json()

                    fasciculation_count = json_data.get('fasciculation_count')
                    all_keypoints = json_data.get('all_keypoints')
                    fps = json_data.get('fps')

            else:
                    print(">> Not a Flask Response object:", response_bulk)

            processed_videos.append({
                "path": f"processed_videos/{base_name}/{output_name}",
                "name": output_name,
                "fasciculation_count": fasciculation_count,
                "fps": fps,
            })

        except KeyError as e:
            return jsonify({
                "success": False,
                "message": f"Missing column in Excel file: {e.args[0]}. Please use the correct template."
            })
        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e) + " Please correct your Excel file."
            })

    TEMP_DATA["latest"] = processed_videos
    return jsonify({"success": True, "redirect_url": url_for("bulk_results")}), 200

@app.route("/results")
def bulk_results():
    videos = TEMP_DATA.get("latest", [])
    df = pd.DataFrame([
        {
            "filename": item.get("name", "NA"),
            "fasciculations": item.get("fasciculation_count", "NA"),
            "fps": item.get("fps", "NA")
        }
        for item in videos
    ])
    
    # Define the path for the Excel file
    unique_id = uuid.uuid4().hex
    filename = f"processed_results_{unique_id}.xlsx"
    excel_path = os.path.join("static", "excel", filename)
    df.to_excel(excel_path, index=False)
    # Store the path in session for download later
    session["excel_filename"] = filename

    return render_template("bulk_results.html", videos=videos , excel_filename=filename)

if __name__ == "__main__":
    app.run(debug=True)