import os
import json
import shutil
import asyncio

from moviepy.editor import ImageSequenceClip
from datetime import datetime
from log_db import create_connection, create_table, get_logs, delete_logs, close_connection, insert_logs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def read_logs(file_path, start=0, end=999999999999999999):
    conn = create_connection(file_path)
    print("Connection: ", conn)
    logs = get_logs(conn, start, end)
    close_connection(conn)
    return logs

def create_project(project_name):
    base_dir = f'./projects/{project_name}/'
    os.makedirs(base_dir + 'src/', exist_ok=True)
    os.makedirs(base_dir + 'outputs/', exist_ok=True)
    os.makedirs(base_dir + 'versions/', exist_ok=True)
    metadata = {
        'current_version': 0,
        'versions': [],
        'redo_stack': []
    }
    with open(base_dir + 'project_metadata.json', 'w') as f:
        json.dump(metadata, f)

def load_project(project_name):
    base_dir = f'./projects/{project_name}/'
    if not os.path.exists(base_dir):
        return {'error': 'Project not found'}, 404
    
    return {'message': 'Project loaded successfully'}

def delete_project(project_name):
    base_dir = f'./projects/{project_name}/'
    shutil.rmtree(base_dir)

def save_version(project_name):
    base_dir = f'./projects/{project_name}/'
    src_dir = base_dir + 'src/'
    with open(base_dir + 'project_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    version_number = metadata['current_version'] + 1
    version_dir = f'{base_dir}versions/version_{version_number}/'
    os.makedirs(version_dir, exist_ok=True)
    
    shutil.copytree(src_dir, version_dir, dirs_exist_ok=True)
    
    metadata['current_version'] = version_number
    metadata['versions'].append({
        'version': version_number,
        'timestamp': datetime.now().isoformat()
    })
    metadata['redo_stack'] = []  # Clear the redo stack
    with open(base_dir + 'project_metadata.json', 'w') as f:
        json.dump(metadata, f)

def undo_change(project_name):
    base_dir = f'./projects/{project_name}/'
    with open(base_dir + 'project_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    if metadata['current_version'] == 0:
        return 'No versions to revert to.'
    
    previous_version = metadata['current_version'] - 1
    version_dir = f'{base_dir}versions/version_{previous_version}/'
    
    # Save current version to redo stack
    metadata['redo_stack'].append(metadata['current_version'])
    
    shutil.rmtree(base_dir + 'src/')
    shutil.copytree(version_dir, base_dir + 'src/', dirs_exist_ok=True)
    
    metadata['current_version'] = previous_version
    metadata['versions'] = metadata['versions'][:-1]
    with open(base_dir + 'project_metadata.json', 'w') as f:
        json.dump(metadata, f)

def redo_change(project_name):
    base_dir = f'./projects/{project_name}/'
    with open(base_dir + 'project_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    if not metadata['redo_stack']:
        return 'No versions to redo.'
    
    redo_version = metadata['redo_stack'].pop()
    version_dir = f'{base_dir}versions/version_{redo_version}/'
    
    shutil.rmtree(base_dir + 'src/')
    shutil.copytree(version_dir, base_dir + 'src/', dirs_exist_ok=True)
    
    metadata['current_version'] = redo_version
    metadata['versions'].append({
        'version': redo_version,
        'timestamp': datetime.now().isoformat()
    })
    with open(base_dir + 'project_metadata.json', 'w') as f:
        json.dump(metadata, f)

def get_versions(project_name):
    base_dir = f'./projects/{project_name}/'
    with open(base_dir + 'project_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    return metadata['versions']

def get_current_version(project_name):
    base_dir = f'./projects/{project_name}/'
    with open(base_dir + 'project_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    return metadata['current_version']

def get_directory_structure(dir_path):
    structure = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if item == 'outputs' or item == 'project.zip':
            continue
        if os.path.isdir(item_path):
            structure.append({item: get_directory_structure(item_path)})
        else:
            structure.append(item)
    return structure

def get_files(project_name):
    project_dir = f'./projects/{project_name}/src/'
    directory_structure = get_directory_structure(project_dir)
    print(directory_structure)
    return directory_structure

def get_file(user_id, project_name, file):
    project_dir = f'./projects/' + str(user_id) + '/' + project_name + '/src/'
    file_path = os.path.join(project_dir, file)
    print(file_path)

    if not os.path.isfile(file_path):
        return {'error': 'File not found'}, 404

    with open(file_path, 'r') as f:
        content = f.read()

    return {'content': content}

def upload_file(project_name, user_id, file, content):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    file_path = os.path.join(project_dir, file)

    with open(file_path, 'w') as f:
        f.write(content)

    return {'message': 'File uploaded successfully'}

def download_project(project_name):
    base_dir = f'./projects/{project_name}/'
    shutil.make_archive(base_dir + 'project', 'zip', base_dir)
    return base_dir + 'project.zip'

async def execute_project(project_name, user_id, outputs=['log'], duration=1):
    base_dir = f'./projects/' + str(user_id) + '/' + project_name + '/'
    project_dir = base_dir + 'src/'
    outputs_dir = base_dir + 'outputs/'

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
            await asyncio.sleep(interval)

        # Convert screenshots to video
        video_filename = outputs_dir + 'video.webm'
        clip = ImageSequenceClip(screenshot_filenames, fps=30)
        clip.write_videofile(video_filename, codec='libvpx')

    if 'log' in outputs:
        # Record logs
        try:
            logs = browser.get_log('browser')
            conn = create_connection(outputs_dir + 'logs.db')
            create_table(conn) # Ensure the table exists before inserting logs
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
        output_files['url'] = 'https://localhost:5000/projects/' + project_name + '/src/index.html'

    return output_files



    
def delete_file(project_name, user_id, file):

    file_path = f'./projects/' + str(user_id) + '/' + project_name + '/src/' + file
    if not os.path.exists(file_path):
        return {'error': 'File not found'}, 404

    if os.path.isfile(file_path):
        os.remove(file_path)
    elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    else:
        return {'error': 'Invalid path'}, 400

    return {'success': 'File or directory deleted'}

def create_file(project_name, user_id, file_path, content=''):
    full_path = os.path.join('projects', str(user_id), project_name, 'src', file_path)
    if os.path.exists(full_path):
        return {'error': 'File already exists'}, 400

    if file_path.endswith('/'):
        # Ensure the directory exists
        os.makedirs(full_path, exist_ok=True)
    else:
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # Create the file
        with open(full_path, 'w') as f:
            f.write(content)  # Write the specified content or an empty string

    return {'success': 'File created'}