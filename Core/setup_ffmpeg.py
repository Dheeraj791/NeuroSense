import os
import platform
import zipfile
import tarfile
import shutil
import requests  

def download_file(url, destination):
    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise error on bad status
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def extract_zip(src, dst):
    with zipfile.ZipFile(src, 'r') as zf:
        zf.extractall(dst)

def extract_tar_xz(src, dst):
    with tarfile.open(src, 'r:xz') as tf:
        tf.extractall(dst)

def setup_ffmpeg():
    system = platform.system()
    bin_dir = os.path.join(os.path.dirname(__file__), 'bin')
    os.makedirs(bin_dir, exist_ok=True)

    if system == "Windows":
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
        zip_path = os.path.join(bin_dir, "ffmpeg.zip")
        download_file(url, zip_path)
        extract_zip(zip_path, bin_dir)
        os.remove(zip_path)

        ffmpeg_exe = None
        for root, _, files in os.walk(bin_dir):
            if "ffmpeg.exe" in files:
                ffmpeg_exe = os.path.join(root, "ffmpeg.exe")
                break

        if not ffmpeg_exe:
            raise RuntimeError("ffmpeg.exe not found after extracting the zip.")

        shutil.copy(ffmpeg_exe, os.path.join(bin_dir, "ffmpeg.exe"))
        print(f"ffmpeg.exe copied to: {os.path.join(bin_dir, 'ffmpeg.exe')}")

    elif system == "Darwin":
        url = "https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip"
        zip_path = os.path.join(bin_dir, "ffmpeg.zip")
        download_file(url, zip_path)
        extract_zip(zip_path, bin_dir)
        os.rename(os.path.join(bin_dir, "ffmpeg"), os.path.join(bin_dir, "ffmpeg-macos"))
        os.chmod(os.path.join(bin_dir, "ffmpeg-macos"), 0o755)
        os.remove(zip_path)

    elif system == "Linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        tar_path = os.path.join(bin_dir, "ffmpeg.tar.xz")
        download_file(url, tar_path)
        extract_tar_xz(tar_path, bin_dir)
        os.remove(tar_path)
        for root, _, files in os.walk(bin_dir):
            if "ffmpeg" in files and not files[0].endswith(".txt"):
                shutil.copy(os.path.join(root, "ffmpeg"), os.path.join(bin_dir, "ffmpeg-linux"))
                os.chmod(os.path.join(bin_dir, "ffmpeg-linux"), 0o755)
                break

    print("FFmpeg setup complete.")

def get_ffmpeg_path():
    system = platform.system()
    bin_dir = os.path.join(os.path.dirname(__file__), 'bin')
    if system == "Windows":
        return os.path.join(bin_dir, "ffmpeg.exe")
    elif system == "Darwin":
        return os.path.join(bin_dir, "ffmpeg-macos")
    else:
        return os.path.join(bin_dir, "ffmpeg-linux")
