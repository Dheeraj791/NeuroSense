
## Testing with Sample Excel File

This project includes a utility function that generates a test Excel file with the correct absolute paths to sample video files, helping automate testing.

### How It Works

- The function `get_test_excel_with_correct_paths()` loads a provided Excel template (`test_data_template.xlsx`) containing placeholder paths.
- It replaces the placeholder `"__VIDEO_PATH__"` with the actual absolute path to the sample video file (`test_video.mp4`).
- The updated Excel file is saved as `test_data_generated.xlsx` in the `sample_data` folder.
- This generated Excel file can be used directly for testing the application without manual path edits.

### Manual Testing Instructions

If you want to test the application manually using sample files:

1. Open the Excel template `test_data_template.xlsx` located in the `sample_data` folder.
2. Replace the placeholder paths (e.g., `"__VIDEO_PATH__"`) with the **absolute paths** to your sample video files on your system.
3. Save the Excel file (under a new name if preferred).
4. Provide this edited Excel file to the application as the test input.

This way, the application will correctly locate and process your sample videos during manual testing.


### Note

All test cases and performance validations were executed on a high-specification machine equipped with:


64-bit Windows 11

Intel Core i7 processor

32 GB RAM

SSD storage

Python 3.10+

The application was tested with both small test videos (~1 MB) and large real-world ultrasound files (up to several GBs).
All functionalities — including single and bulk video uploads, Excel integration, real-time previews, and fasciculation detection — were successfully verified and passed across all scenarios.

If any test case fails due to a timeout or resource limit, please retry the operation. 
