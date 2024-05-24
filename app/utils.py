import os
import shutil
from .models import User
from . import db
from datetime import datetime
from moviepy.editor import ImageSequenceClip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import asyncio
from .logs import create_connection, create_table, insert_logs, delete_logs, close_connection
import time



def get_file(user_id, project_name, file):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    file_path = os.path.join(project_dir, file)
    
    if not os.path.isfile(file_path):
        return {'error': 'File not found'}, 404

    with open(file_path, 'r') as f:
        content = f.read()

    return {'content': content}
import sqlite3

def read_logs(logs_path, start=0, end=999999999999999999):
    try:
        conn = sqlite3.connect(logs_path)
        cursor = conn.cursor()
        
        # Fetch logs within the specified range
        cursor.execute("SELECT level, message, source, timestamp FROM logs WHERE id BETWEEN ? AND ?", (start, end))
        logs = cursor.fetchall()
        
        # Format logs as a list of dictionaries
        log_entries = []
        for log in logs:
            log_entries.append({
                'level': log[0],
                'message': log[1],
                'source': log[2],
                'timestamp': log[3]
            })
        
        conn.close()
        return log_entries
    
    except sqlite3.Error as e:
        print(f"SQLite error: {str(e)}")
        return {'error': str(e)}


def execute_project(project_name, user_id, outputs=['log'], duration=10):
    project_dir = f'app/projects/{user_id}/{project_name}/src/'
    outputs_dir = f'app/projects/{user_id}/{project_name}/outputs/'



    # Execute the project here

    # Clear the logs
    conn = create_connection(outputs_dir + 'logs.db')
    delete_logs(conn)
    close_connection(conn)

    # Configure Chrome options and enable logging
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--window-size=512,512")

    # Create desired capabilities
    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

    # Merge options with capabilities
    chrome_options.set_capability('goog:loggingPrefs', capabilities['goog:loggingPrefs'])

    # Open the browser
    index_file_path = project_dir + 'index.html'
    browser = webdriver.Chrome(options=chrome_options)
    file_url = 'file://' + os.path.abspath(index_file_path)
    print("Loading URL:", file_url)
    browser.get(file_url)

    # Define a temporary directory to store screenshots
    screenshots_dir = outputs_dir + 'screenshots/'
    os.makedirs(screenshots_dir, exist_ok=True)

    # Take screenshots
    screenshot_filenames = []
    interval = 1

    if 'image' in outputs:
        # Take a single screenshot
        print('Taking screenshot')
        screenshot_filename = f'{outputs_dir}image.png'
        browser.save_screenshot(screenshot_filename)
        screenshot_filenames.append(screenshot_filename)

    if 'video' in outputs:
        # Record a video
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < duration:
            screenshot_filename = f'{screenshots_dir}screenshot-{len(screenshot_filenames)}.png'
            print(screenshot_filename)
            browser.save_screenshot(screenshot_filename)
            screenshot_filenames.append(screenshot_filename)
            time.sleep(interval)

        # Convert screenshots to video
        video_filename = outputs_dir + 'video.webm'
        clip = ImageSequenceClip(screenshot_filenames, fps=30)
        clip.write_videofile(video_filename, codec='libvpx')

    if 'log' in outputs:
        # Record logs
        try:
            logs = browser.get_log('browser')
            conn = create_connection(outputs_dir + 'logs.db')
            create_table(conn)  # Ensure the table exists before inserting logs
            insert_logs(conn, [(log['level'], log['message'], log['source'], log['timestamp']/1000) for log in logs])
            close_connection(conn)
        except Exception as e:
            return {'error': str(e)}
        
    # Close the browser
    browser.quit()

    # Clean up the screenshots
    shutil.rmtree(screenshots_dir)

    # Return the output files
    output_files = {}
    if 'image' in outputs:
        output_files['image'] = 'image.png'
    if 'video' in outputs:
        output_files['video'] = 'video.webm'
    if 'log' in outputs:
        output_files['log'] = 'logs.db'
    if 'url' in outputs:
        output_files['url'] = f'https://localhost:5000/projects/{user_id}/{project_name}/src/index.html'

    return output_files


def upload_file(project_name, user_id, file, content):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    file_path = os.path.join(project_dir, file)

    with open(file_path, 'w') as f:
        f.write(content)

    return {'message': 'File uploaded successfully'}

def delete_file(project_name, user_id, file_path):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    full_path = os.path.join(project_dir, file_path)

    if os.path.isfile(full_path):
        os.remove(full_path)
    elif os.path.isdir(full_path):
        shutil.rmtree(full_path)
    else:
        return {'error': 'File or directory not found'}, 404

def create_file(project_name, user_id, file_path):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    full_path = os.path.join(project_dir, file_path)

    with open(full_path, 'w') as f:
        f.write('')

    return {'message': 'File created successfully'}
