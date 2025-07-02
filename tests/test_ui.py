import os
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from selenium.common.exceptions import WebDriverException
from urllib.parse import urlparse
from tests.test_util import get_test_excel_with_correct_paths
from tests.test_util import get_single_test_video_path


class NeurosenseUITest(unittest.TestCase):
    @classmethod
    
    def setUpClass(cls):
        # Check if host is reachable
        try:
            response = requests.get("http://127.0.0.1:5000", timeout=10)
            if response.status_code != 200:
                raise ConnectionError(f"Flask app returned status {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Could not reach the Flask app at http://127.0.0.1:5000. "
                               f"Make sure the server is running.\nError: {e}")

        # If host is reachable, launch browser and maximize window
        try:
            cls.driver = webdriver.Chrome()
            cls.driver.get("http://127.0.0.1:5000")
            cls.driver.maximize_window()
        except WebDriverException as e:
            raise RuntimeError(f"Could not launch Chrome WebDriver.\nError: {e}")
        
    def pytest_sessionstart(session):
            print(
            """\n\n
            # TESTING IS FOR DEVELOPERS ONLY, USE AT YOUR OWN RISK 
            #
            #      _   _                        _____                       
            #     | \\ | |                      / ____|                      
            #     |  \\| | ___  _   _ _ __ ___ | (___   ___ _ __ __ _ _ _ _ 
            #     | . ` |/ _ \\| | | | '__/ _ \\ \\___ \\ / __| '__/ _` | | | |
            #     | |\\  | (_) | |_| | | |  __/ ____) | (__| | | (_| | |_| |
            #     |_| \\_|\\___/ \\__,_|_|  \\___||_____/ \\___|_|  \\__,_|\\__, |
            #                                                          
            #
            # TESTING IS FOR DEVELOPERS ONLY, USE AT YOUR OWN RISK 
            \n\n"""
            )

    def test_1_single_video_upload(self):
        driver = self.driver

        combinations = [("BB", "longitudinal"), ("BB", "transverse")]

        for muscle_value, probe_value in combinations:
            driver.get("http://127.0.0.1:5000")  # Reload the page for each combination

            # Select dropdown values
            muscle_dropdown = Select(driver.find_element(By.ID, "muscleGroup"))
            probe_dropdown = Select(driver.find_element(By.ID, "probeOrientation"))
            muscle_dropdown.select_by_value(muscle_value)
            probe_dropdown.select_by_value(probe_value)

            # Upload vidoe
            video_path = get_single_test_video_path()
            self.assertTrue(os.path.exists(video_path), f"Test video not found at: {video_path}")

            upload_input = driver.find_element(By.ID, "singleVideoUpload")
            upload_input.send_keys(video_path)

            # Submit upload
            upload_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Upload Single Video')]")
            upload_btn.click()

            # Wait for progress bar
            WebDriverWait(driver, 500).until(
                EC.visibility_of_element_located((By.ID, "progressBarContainer"))
            )

            # Wait for summary box
            WebDriverWait(driver, 500).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "summary-box"))
            )

            summary_box = driver.find_element(By.CLASS_NAME, "summary-box")
            self.assertTrue(summary_box.is_displayed(), f"Summary not visible for {muscle_value}-{probe_value}")

    def test_2_single_video_results_page(self):
        driver = self.driver

        summary = WebDriverWait(driver, 500).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "summary-box"))
        )
        self.assertIn("Filename:", summary.text)

        # Extract and validate route
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        self.assertIn("/result", parsed_url.path, f"Expected route to include '/result', got '{parsed_url.path}'")

        video = driver.find_element(By.TAG_NAME, "video")
        self.assertTrue(video.is_displayed())

        plot = driver.find_element(By.ID, "plot")
        self.assertTrue(plot.is_displayed())

        download_btn = driver.find_element(By.LINK_TEXT, "Download Processed Video")
        self.assertTrue(download_btn.is_displayed())

        print(" Single video upload & result test passed.")


    def test_3_bulk_video_upload(self):
        driver = self.driver
        driver.get("http://127.0.0.1:5000")

        bulk_section = driver.find_element(By.XPATH, "//h2[text()='Bulk Video Upload']")
        driver.execute_script("arguments[0].scrollIntoView(true);", bulk_section)

        # Upload Excel file
        excel_input = WebDriverWait(driver, 500).until(
            EC.presence_of_element_located((By.ID, "bulkExcelUpload"))
        )
        excel_path = get_test_excel_with_correct_paths()
        self.assertTrue(os.path.exists(excel_path), f"Excel file not found at: {excel_path}")
        excel_input.send_keys(excel_path)

        upload_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Upload Excel File')]")
        upload_btn.click()

        WebDriverWait(driver, 500).until(
            EC.visibility_of_element_located((By.ID, "progressBarContainer_bulk"))
        )

    def test_4_bulk_results_check(self):
        driver = self.driver

        # Ensure the main featured video is present 
        try:
            # Wait for main video to be visible 
            featured_video = WebDriverWait(driver, 500).until(
                EC.visibility_of_element_located((By.ID, "main-video"))
            )

            # Scroll it into view in case it's off-screen
            driver.execute_script("arguments[0].scrollIntoView(true);", featured_video)

            # Wait until video is fully loaded
            WebDriverWait(driver, 500).until(
                lambda d: d.execute_script(
                    "let v = document.getElementById('main-video'); return v && v.readyState === 4;"
                )
            )

            # Final assert
            self.assertTrue(featured_video.is_displayed(), "Main video is not displayed on result page")

        except Exception as e:
            print("testing working")
            raise e

        # Extract and validate route
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        self.assertIn("/results", parsed_url.path, f"Expected route to include '/results', got '{parsed_url.path}'")

        # Ensure the graph container and plot are visible 
        graph = WebDriverWait(driver, 500).until(
            EC.presence_of_element_located((By.ID, "plot"))
        )
        self.assertTrue(graph.is_displayed())

        # Ensure table with video metadata exists 
        table = WebDriverWait(driver, 500).until(
            EC.presence_of_element_located((By.CLASS_NAME, "video-metadata-table"))
        )
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertGreater(len(rows), 0, "No rows in video summary table")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            self.assertEqual(len(cells), 5, "Each row should have 5 columns")

            # Validate each expected column 
            radio_input = cells[0].find_element(By.TAG_NAME, "input")
            self.assertEqual(radio_input.get_attribute("type"), "radio")

            file_name = cells[1].text
            self.assertTrue(file_name.endswith(".mp4"))

            download_link = cells[2].find_element(By.TAG_NAME, "a")
            self.assertIn("Download", download_link.text)

            fas_text = cells[3].text
            self.assertIn("Fas", fas_text)

            fps_text = cells[4].text
            self.assertIn("FPS", fps_text)

            print("Bulk results page structure and content verified.")

                
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()