# NeuroSense Test Suite

This directory contains the end-to-end test suite for NeuroSense, a Flask-based web application for muscle ultrasound video processing and fasciculation detection.

---

## Overview

The tests use Selenium WebDriver to automate browser interactions with the NeuroSense web app hosted locally at `http://127.0.0.1:5000`. They validate:

- Single video upload and processing workflows  
- Bulk video upload via Excel file and result visualization  
- Handling of invalid files and error dialogs  
- UI elements like dropdowns, buttons, video players, progress bars, and alerts  
- Navigation and page reloads without errors  
- Form validation and UI constraints  

---

## Test Descriptions

| Test Name                      | Purpose                                                                                              |
|-------------------------------|----------------------------------------------------------------------------------------------------|
| `test_1_single_video_upload`    | Uploads single video with various muscle and probe settings; checks for progress and summary UI.   |
| `test_2_single_video_results_page` | Validates result page elements: summary box, video player, plot.                                 |
| `test_3_invalid_single_video_upload` | Uploads invalid video and confirms custom error alert with internal server error message.        |
| `test_4_bulk_video_upload`       | Uploads bulk Excel with valid video paths; waits for bulk upload progress bar.                     |
| `test_5_bulk_results_check`      | Checks bulk results page UI: featured video, plots, metadata table with correct structure.         |
| `test_6_invalid_excel_upload`    | Uploads invalid Excel and verifies custom error alert appears.                                    |
| `test_7_page_reload_no_errors`   | Refreshes page and checks page title to ensure no errors on reload.                               |
| `test_8_navigation_links_work`   | Checks all navigation links on site lead to expected pages without error.                         |
| `test_9_multiple_file_selection_ui_block` | Ensures single video upload input does not allow multiple file selection.                  |
| `test_10_empty_single_video_submission` | Attempts empty video upload and verifies form validation alert is shown.                       |


## Requirements

- Python 3.x  
- `selenium` Python package  
- A working Chrome browser and compatible [ChromeDriver](https://chromedriver.chromium.org/) installed and on your system PATH  
- Flask app running locally at `http://127.0.0.1:5000` before running tests  
- Test asset files (videos and Excel sheets) accessible at paths returned by helper functions in `tests.test_util`  

---

## Running the Tests

### Prerequisites

- The **NeuroSense Flask app must be running** locally at:

  ```
  http://127.0.0.1:5000
  ```

- Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

- Ensure you have:

  - Google Chrome installed
  - [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) that matches your Chrome version
  - `chromedriver` in your system PATH

---

### Run All Tests

Once you are in tests directory, follow below command:

Using `pytest`:

```bash
pytest test_ui.py
```

---
