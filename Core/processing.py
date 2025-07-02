import cv2
import numpy as np
import os
import subprocess
from flask import jsonify
from Core.setup_ffmpeg import setup_ffmpeg, get_ffmpeg_path

current_dir = os.path.dirname(os.path.abspath(__file__))

parent_dir = os.path.dirname(current_dir)

bin_dir = os.path.join(parent_dir, 'bin')

expected_names = ['ffmpeg', 'ffmpeg.exe', 'ffmpeg-macos', 'ffmpeg-linux', 'ffmpeg-win.exe']

print("Checking FFmpeg presence in:", bin_dir)

ffmpeg_present = False
if os.path.exists(bin_dir):
    for name in expected_names:
        full_path = os.path.join(bin_dir, name)
        if os.path.isfile(full_path):
            ffmpeg_present = True
            print(f"Found ffmpeg executable: {name}")
            break

if not ffmpeg_present:
    print("Setting up FFmpeg...")
    setup_ffmpeg()
else:
    print("FFmpeg already exists. Skipping download.")

# Get usable ffmpeg path
ffmpeg_path = get_ffmpeg_path()

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
    ffmpeg_path = get_ffmpeg_path()  
    temp_path = input_path.replace(".mp4", "_temp.mp4")

    cmd = [
        ffmpeg_path,
        "-i", input_path,
        "-movflags", "faststart",
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "3.1",
        "-c:a", "aac",
        "-b:a", "128k",
        temp_path,
    ]
    try:
        subprocess.run(cmd, check=True)
        os.replace(temp_path, input_path) 
        return input_path
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
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

            # Visual overlays 
            centroids = []
            for k in keypoints:
                x, y = int(k.pt[0]), int(k.pt[1])
                centroids.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Red dot

            all_keypoints.append(centroids)

            # Connect blobs with lines (one line for each pair)
            for i in range(len(centroids) - 1):  
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