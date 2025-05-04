from flask import Flask, request, send_file, redirect, url_for, render_template, session
import pandas as pd
import os
from tempfile import NamedTemporaryFile
import multiprocessing
from flask import Flask, request, jsonify, send_file
from tkinter import filedialog, Tk
import cv2
import numpy as np
import uuid
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # Must be set for using session #dummy string used 

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join('static', 'processed')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

upload_dir = 'uploads'
os.makedirs(upload_dir, exist_ok=True)  # Create if not exists


class ForegroundDetector:
    def __init__(self, num_gaussians, min_background_ratio, initial_variance, learning_rate, num_training_frames=500, adapt_learning_rate=True):
        self.num_gaussians = num_gaussians
        self.min_background_ratio = min_background_ratio
        self.initial_variance = initial_variance
        self.adapt_learning_rate = adapt_learning_rate
        self.num_training_frames = num_training_frames
        self.learning_rate = learning_rate
        self.time = 0
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=num_training_frames,
                                                                detectShadows=False)
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
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=self.num_training_frames,
                                                                detectShadows=False)
        self.bg_subtractor.setBackgroundRatio(self.min_background_ratio)
        self.bg_subtractor.setNMixtures(self.num_gaussians)
        self.time = 0

def process_video(input_video_path, output_video_path, params):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {input_video_path}")
        return

    # Create a ForegroundDetector instance using the provided parameters
    detector = ForegroundDetector(**params)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Use MP4 codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Get foreground mask
        fg_mask = detector.step(frame)

        if frame_count > 500:
            # Detect blobs in the foreground mask
            keypoints = blob_detector.detect(fg_mask)

            # Extract centroids
            centroids = []
            for k in keypoints:
                x, y = int(k.pt[0]), int(k.pt[1])
                centroids.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Red dot

            # Connect blobs with lines
            for i in range(len(centroids)):
                for j in range(i + 1, len(centroids)):
                    pt1 = centroids[i]
                    pt2 = centroids[j]
                    cv2.line(frame, pt1, pt2, (255, 255, 0), 1)  # Cyan line

        # Write the frame (with overlays if any)
        out.write(frame)  

        frame_count += 1


    cap.release()
    out.release()
    print(f"Finished processing {input_video_path}")


@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return "No video file provided", 400

    video = request.files['video']
    muscle_group = request.form.get('muscle_group')
    probe_orientation = request.form.get('probe_orientation')
    filename = secure_filename(video.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    unique_id = str(uuid.uuid4())
    base, ext = os.path.splitext(filename)
    saved_name = f"{base}_{unique_id}{ext}"
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
    video.save(input_path)

    output_filename = f"processed_{unique_id}.mp4"  # not .avi
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

    # Define parameter map
    param_map = {
        ('BB', 'longitudinal'): {
            "num_gaussians": 5,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('BB', 'transverse'): {
            "num_gaussians": 3,
            "min_background_ratio": 0.80,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('MG', 'transverse'): {
            "num_gaussians": 3,
            "min_background_ratio": 0.85,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('MG', 'longitudinal'): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('TRAP', 'transverse'): {
            "num_gaussians": 4,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('TRAP', 'longitudinal'): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.5,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('RA', 'transverse'): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('RA', 'longitudinal'): {
            "num_gaussians": 5,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.05,
            "num_training_frames": 500,
            "adapt_learning_rate": True
        },
        ('TP', 'transverse'): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.005,
            "num_training_frames": 100,
            "adapt_learning_rate": True
        },
        ('TP', 'longitudinal'): {
            "num_gaussians": 3,
            "min_background_ratio": 0.90,
            "initial_variance": 30 * 2,
            "learning_rate": 0.005,
            "num_training_frames": 300,
            "adapt_learning_rate": True
        }
    }

    params = param_map.get((muscle_group, probe_orientation), {
        "num_gaussians": 5,
        "min_background_ratio": 0.7,
        "initial_variance": 30,
        "learning_rate": 0.01,
        "num_training_frames": 500,
        "adapt_learning_rate": True
    })
   
    process_video(input_path, output_path, params)

    session['processed_video'] = output_filename

    # Redirect to the result page 
    return redirect(url_for('result'))

@app.route('/result')
def result():
    processed_video = session.get('processed_video')
    if not processed_video:
        return "No processed video found", 404
    return render_template('result.html', video_path=url_for('static', filename=f'processed/{processed_video}'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_template', methods=['GET'])
def download_template():
    try:
        # Define the columns for the template
        columns = ["trial_name", "muscle_group", "probe_orientation", "file_path"]
        
        # Create an empty DataFrame
        df = pd.DataFrame(columns=columns)
    
        # Create a temporary file to save the Excel template
        with NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            template_path = temp_file.name
            df.to_excel(template_path, index=False)
        
        # Return the file to the user for download
        return send_file(template_path, as_attachment=True, download_name="video_upload_template.xlsx")
    
    except Exception as e:
        print(f"Error generating Excel file: {e}")
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

@app.route('/select-folder', methods=['POST'])
def select_folder():
    # Run Tkinter folder selection in a separate process
    with multiprocessing.Pool(1) as pool:
        folder_path = pool.apply(select_folder_gui)

    if not folder_path:
        return jsonify({'success': False, 'message': 'No folder selected'})

    files = os.listdir(folder_path)  # Get all file names
    file_paths = [os.path.join(folder_path, file) for file in files]

    # Save to Excel
    df = pd.DataFrame({'File Name': files, 'Full Path': file_paths})
    output_file = os.path.join(folder_path, "files_list.xlsx")
    df.to_excel(output_file, index=False)

    return jsonify({'success': True, 'file_url': f'/download-excel?path={output_file}'})

@app.route('/download-excel')
def download_excel():
    file_path = request.args.get('path')
    return send_file(file_path, as_attachment=True)

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    file = request.files['file']
    if not file:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    # Create upload directory
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)

    # Save uploaded Excel file
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Read Excel or CSV
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Define GMM parameters
    params = {
        'num_gaussians': 5,
        'min_background_ratio': 0.7,
        'initial_variance': 15.0,
        'learning_rate': 0.01,
        'num_training_frames': 500,
        'adapt_learning_rate': True
    }

    # Create a unique subfolder for this upload in static
    base_name = os.path.splitext(filename)[0]
    subfolder_path = os.path.join('static', 'processed_videos', base_name)
    os.makedirs(subfolder_path, exist_ok=True)

    processed_videos = []

    # Process each row in Excel
    for idx, row in df.iterrows():
        video_path = row['Full_Path']
        muscle_group = row['muscle_group']
        probe_orientation = row['probe_orientation']

        output_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_processed.mp4"
        output_path = os.path.join(subfolder_path, output_name)

        print(f"Processing: {video_path}")
        process_video(video_path, output_path, params)

        # Append relative path for frontend
        processed_videos.append({
            'path': f"processed_videos/{base_name}/{output_name}",
            'name': output_name
        })

    print("Processed videos:", processed_videos)

    # Render the results page
    session['processed_videos'] = processed_videos
    return redirect(url_for('bulk_results'))

@app.route('/results')
def bulk_results():
    videos = session.get('processed_videos', [])
    print("Videos in session:", videos)  # Debug line
    return render_template('bulk_results.html', videos=videos)


if __name__ == '__main__':
    app.run(debug=True)