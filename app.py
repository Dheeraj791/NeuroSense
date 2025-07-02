from flask import Flask, request, send_file, redirect, url_for, render_template, session ,jsonify
import pandas as pd
import os, threading
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
import json
from flask import Response
from Core.processing import process_video, ForegroundDetector

app = Flask(__name__)
app.secret_key = (
    "test_123"  # Must be set for using session #dummy string used
)
CORS(app)  # Enable Cross-Origin Resource Sharing

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["PROCESSED_FOLDER"] = os.path.join("static", "processed")
keypoints_dir = os.path.join("static", "keypoints")
excel_dir = os.path.join("static", "excel")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROCESSED_FOLDER"], exist_ok=True)
os.makedirs(keypoints_dir, exist_ok=True)
os.makedirs(excel_dir, exist_ok=True)

upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)  
TEMP_DATA = {}
TASK_STATUS = {}

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

    output_filename = f"processed_{unique_id}.mp4"  
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)

    # Define parameter map (Optimsed parameters for each muscle group and probe orientation)
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

        keypoints_id = str(uuid.uuid4())
        keypoints_filename = f"{keypoints_id}.json"
        keypoints_path = os.path.join("static", "keypoints", keypoints_filename)

        with open(keypoints_path, "w") as f:
            json.dump(all_keypoints, f)

    else:
        print(">> Not a Flask Response object:", response)
    
    

    # Redirect to the result page
    return redirect(url_for("result",
                        processed=output_filename,
                        count=fasciculation_count,
                        keypoints=keypoints_filename,
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

    keypoints_path = os.path.join("static","keypoints", all_keypoints_json)

    with open(keypoints_path, "r") as f:
        all_keypoints = json.load(f)

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

    task_id = str(uuid.uuid4())
    TASK_STATUS[task_id] = {"current_index": 1, "total": len(df), "status": "processing"}

    def threaded_bulk_processing():
        with app.app_context():

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
                        "all_keypoints": all_keypoints

                    })

                    TASK_STATUS[task_id]["current_index"] = idx + 1
                    print("here", TASK_STATUS[task_id]["current_index"], "of", TASK_STATUS[task_id]["total"])

                except KeyError as e:
                    TASK_STATUS[task_id]["status"] = "error"
                    TASK_STATUS[task_id]["message"] = f"Missing column in Excel file: {e.args[0]}. Please use the correct template."
                    break
                except Exception as e:
                    TASK_STATUS[task_id]["status"] = "error"
                    TASK_STATUS[task_id]["message"] = f"Error processing row {idx}: {str(e)}"
                    break
                
            else:
                TEMP_DATA[task_id] = processed_videos
                TASK_STATUS[task_id]["status"] = "done"
                print(f"Bulk processing completed for task {task_id}. Processed {len(processed_videos)} videos.")
            
        return  

    thread = threading.Thread(target=threaded_bulk_processing)
    thread.start()

    return jsonify({
            "success": True,
            "redirect_url": url_for("bulk_results", task_id=task_id),
            "task_id": task_id   # so frontend bulk-upload can poll and get task status
        }), 200

@app.route("/progress_index/<task_id>")
def get_index_progress(task_id):
    task = TASK_STATUS.get(task_id)
    if not task:
        return jsonify({"success": False, "message": "Invalid task ID"}), 404

    current_index = int(task.get("current_index") or 0)
    total = int(task.get("total") or 0)
    status = task.get("status") or "in_progress"

    return jsonify({
        "success": True,
        "current_index": current_index,
        "total": total,
        "status": status
    })

@app.route("/results")
def bulk_results():
    task_id = request.args.get("task_id")
    videos = TEMP_DATA.get(task_id, [])   
    print(f"Bulk results for task {task_id}: {len(videos)} videos processed.")
    if not videos:
        return render_template("bulk_results.html", videos=[], excel_filename=None)
    
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