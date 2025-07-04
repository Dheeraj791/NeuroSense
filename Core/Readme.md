# Fasciculation Detection Core Module

This module implements the core logic for detecting fasciculations in ultrasound videos using foreground motion segmentation and blob tracking.

## Key Features

- **Foreground Subtraction:**  
  Uses OpenCV’s `createBackgroundSubtractorMOG2` to model background and isolate motion.

- **Blob Detection:**  
  Applies `SimpleBlobDetector` to highlight candidate fasciculations in each frame based on area.

- **Temporal Event Logic:**  
  Fasciculations are counted only when motion is sustained across consecutive frames within a short time window (~200 ms).

- **Overlay Generation:**  
  Visual feedback includes:
  - Red circles at detected keypoints.
  - Cyan lines connecting nearby blobs within a frame.

- **Video Optimization:**  
  Uses FFmpeg to re-encode videos for browser compatibility (`faststart`, `libx264`, `aac`).

## Usage

The module includes the following major components:

### `ForegroundDetector`

A wrapper around OpenCV’s MOG2 background subtractor, configured for clinical ultrasound data.

```python
detector = ForegroundDetector(
    num_gaussians=5,
    min_background_ratio=0.7,
    initial_variance=15,
    learning_rate=0.01
)
fg_mask = detector.step(frame)
