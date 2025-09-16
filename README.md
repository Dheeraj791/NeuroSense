
<p>
  <img src="static/images/NEuroSense.png" alt="Logo" width="180" style="border: 3px ridge #ccc; padding: 5px;">
</p>

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
![Platforms](https://img.shields.io/badge/platform-macOS%20|%20Windows%20|%20Linux-green)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17138130.svg)](https://doi.org/10.5281/zenodo.17138130)


# NeuroSense

Fasciculations are small, involuntary muscle twitches that can be early signs of serious conditions like Motor Neuron Disease (MND). Early detection is important for timely diagnosis and treatment. NeuroSense is a tool designed to detect these twitches using video analysis.

NeuroSense – A tool based on Gaussian Mixture Models for detecting involuntary muscle twitch movements, known as fasciculations, through foreground detection.

## Motivation

We initially developed the system in MATLAB [Bibbings et al. (2019)] using Gaussian Mixture Models (GMM) for background subtraction. While effective, MATLAB has limitations in expanding and testing advanced methods. Python, with its rich set of machine learning and computer vision libraries, offers a better platform for future development.

We have now successfully migrated our code to Python using OpenCV’s BackgroundSubtractorMOG2, which is also GMM-based. The results are promising, showing clear detection of subtle twitch movements.

With Python, NeuroSense can grow into a smarter, more accurate tool, helping clinicians and other researchers identify fasciculations earlier. 

Our goal is to support earlier diagnosis of MND and related conditions through accessible and reliable technology.


## Product Highlights

<p align="center">
  <img src="static/images/image_product.png" alt="Product Preview" width="800" height="450" style="border: 4px ridge #ccc;">
</p>


## Architecture

<p align="center">
<img src="static/images/architecture.png" alt="Product Preview"
     style="width: 800px; max-width: 1000px; height: 415px; border: 4px ridge #ccc;">
</p>


## Installation

Follow the steps below to set up and run the Flask application locally:

1. **Clone the Repository**

    ```bash
      git clone https://github.com/Dheeraj791/NeuroSense.git
      cd NeuroSense
    ```

2. **(Optional) Create and Activate a Virtual Environment**

    - **macOS/Linux:**
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

    - **Windows (CMD):**
      ```cmd
      python -m venv venv
      venv\Scripts\activate
      ```

    - **Windows (PowerShell):**
      ```powershell
      python -m venv venv
      venv\Scripts\Activate.ps1
      ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Environment Variables**

    - **macOS/Linux:**
      ```bash
      export FLASK_APP=app.py
      export FLASK_ENV=development
      ```

    - **Windows (CMD):**
      ```cmd
      set FLASK_APP=app.py
      set FLASK_ENV=development
      ```

    - **Windows (PowerShell):**
      ```powershell
      $env:FLASK_APP = "app.py"
      $env:FLASK_ENV = "development"
      ```

5. **Run the Application**

    ```bash
    flask run
    ```

6. **Visit the App**

    Open your browser and go to:  
    [http://127.0.0.1:5000](http://127.0.0.1:5000)


    
## Features

### Single Video Upload
Upload a single ultrasound video along with its muscle group and probe orientation.
This feature is designed to support large ultrasound files (GB-scale).

A small 1-2 MB test sample video is included for functionality testing purposes.

### Bulk Video Upload via Excel
Upload an entire folder of ultrasound videos using select folder functionality, automatically generate an Excel template, fill in details such as muscle group and probe orientation, and submit it for processing.
This enables batch analysis for high-throughput use cases or larger clinical datasets.

### Live Video Previews & Fasciculation Visualization
After processing, the application provides live previews of all videos.
Detected fasciculations are overlaid in real time, and an interactive graph shows their distribution across the video timeline for easy verification and interpretation.

### Fullscreen Viewing Mode
All processed videos can be expanded to fullscreen, enhancing clarity during analysis and review of subtle fasciculation patterns.



## Contributing

Contributions are always welcome!

see [contributing.md](contributing.md) for ways to get started.

please adhere to this project's [code of conduct](code_of_conduct.md).


## Related Paper

Here are some related projects

[Bibbings et al. (2019)](https://www.sciencedirect.com/science/article/pii/S0301562919300274)

## Citation

If you use **NeuroSense** in your research, please cite:

> Pandey, Dheeraj. (2025). *NeuroSense: Automated fasciculation detection in ultrasound imaging* (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.17138130




## Repo structure

```

├─ .DS_Store
├─ .github
│  └─ workflows
│     └─ paper.yml
├─ .gitignore
├─ Core
│  ├─ Readme.md
│  ├─ __init__.py
│  ├─ processing.py
│  └─ setup_ffmpeg.py
├─ LICENSE
├─ README.md
├─ app.py
├─ code_of_conduct.md
├─ contributing.md
├─ joss-paper
│  └─ figures
│     └─ hl_architecture.png
├─ paper.bib
├─ paper.md
├─ requirements.txt
├─ static
│  ├─ .DS_Store
│  ├─ css
│  │  ├─ alert.css
│  │  ├─ bulk_results.css
│  │  ├─ home.css
│  │  ├─ result.css
│  │  └─ style.css
│  ├─ images
│  │  ├─ NEuroSense.png
│  │  ├─ architecture.png
│  │  ├─ background.jpg
│  │  └─ image_product.png
│  ├─ js
│  │  ├─ .DS_Store
│  │  ├─ alert.js
│  │  ├─ config.js
│  │  └─ script.js
│  └─ logo
│     ├─ .DS_Store
│     └─ logo.png
├─ templates
│  ├─ bulk_results.html
│  ├─ index.html
│  └─ result.html
└─ tests
   ├─ .DS_Store
   ├─ Readme.md
   ├─ __init__.py
   ├─ sample_data
   │  ├─ README.md
   │  ├─ test_data_template.xlsx
   │  └─ test_video.mp4
   ├─ test_ui.py
   └─ test_util.py
```

## Feedback

If you have any feedback, please reach out to us at pandey.dheeraj457@gmail.com
