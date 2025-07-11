import os
import pandas as pd
import tempfile

def get_test_excel_with_correct_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_data"))
    video_path = os.path.join(base_dir, "test_video.mp4")
    template_path = os.path.join(base_dir, "test_data_template.xlsx")

    # Load the Excel template
    df = pd.read_excel(template_path)

    # Replace placeholder with the absolute video path
    df['Full_Path'] = df['Full_Path'].apply(lambda x: video_path if x == "__VIDEO_PATH__" else x)

    # Save the generated Excel to a temp file
    temp_path = os.path.join(base_dir, "test_data_generated.xlsx")
    df.to_excel(temp_path, index=False)
    print(f"Generated test Excel file at: {temp_path}")
    return temp_path

def get_single_test_video_path():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_data"))
    video_path = os.path.join(base_dir, "test_video.mp4")
    print(f"Using test video path: {video_path}")
    return video_path

def get_invalid_excel_path():
    # Create a temporary non-Excel file
    invalid_path = os.path.join(tempfile.gettempdir(), "not_an_excel.txt")
    with open(invalid_path, "w") as f:
        f.write("This is not a valid Excel file.")
    return invalid_path

def get_invalid_video_path():
    # Create a temporary non-video file
    invalid_path = os.path.join(tempfile.gettempdir(), "not_a_video.txt")
    with open(invalid_path, "w") as f:
        f.write("This is not a valid video file.")
    return invalid_path