from flask import Flask, render_template, send_file # type: ignore
import pandas as pd
import os
from tempfile import NamedTemporaryFile
import multiprocessing
from flask import Flask, request, jsonify, send_file
from tkinter import filedialog, Tk

app = Flask(__name__)

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
    root.withdraw()  # Hide the main Tkinter window
    folder_path = filedialog.askdirectory()  # Open folder selection dialog
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


if __name__ == '__main__':
    app.run(debug=True)
