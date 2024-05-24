import os
import shutil
from .models import User

def get_file(user_id, project_name, file):
    project_dir = f'./projects/{user_id}/{project_name}/src/'
    file_path = os.path.join(project_dir, file)
    
    if not os.path.isfile(file_path):
        return {'error': 'File not found'}, 404

    with open(file_path, 'r') as f:
        content = f.read()

    return {'content': content}

def read_logs(file_path, start=0, end=999999999999999999):
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            lines = content.split('\n')
            return lines[start:end]
    except Exception as e:
        print(f"Error reading logs: {str(e)}")
        return []


async def execute_project(project_name, user_id, outputs, duration):
    # Implement the logic to execute the project
    pass

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
