from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import time


from project import load_project, download_project, get_directory_structure, get_files, get_file, upload_file, execute_project, read_logs




app = Flask(__name__)

PROJECTS_DIR = os.path.join(os.getcwd(), 'projects')
project_name = 'projects/cat'

# load the project
load_project(project_name)


# serve the editor

@app.route('/')
def index():
    return render_template('editor/index.html')

# serve static files
@app.route('/editor/<filename>')
def serve_static(filename):
    return send_from_directory('editor', filename)

@app.route('/project/<project>/src')
def serve_project(project):
    project_dir = os.path.join(PROJECTS_DIR, project + '/src')
    return send_from_directory(project_dir, 'index.html')

@app.route('/projects/<project>/src/<filename>')
def serve_project_file(project, filename):
    project_dir = os.path.join(PROJECTS_DIR, project + '/src')
    return send_from_directory(project_dir, filename)

# server any other file wihtin any folder wihtin the projects directory
@app.route('/projects/<project>/src/<folder>/<filename>')
def serve_project_folder_file(project, folder, filename):
    project_dir = os.path.join(PROJECTS_DIR, project + '/src/' + folder)
    return send_from_directory(project_dir, filename)

@app.route('/projects/<project>/outputs/<filename>')
def serve_project_outputs(project, filename):
    project_dir = os.path.join(PROJECTS_DIR, project, 'outputs')
    return send_from_directory(project_dir, filename)


@app.route('/logs', methods=['POST'])
def request_logs():
    data = request.get_json()
    start = int(data.get('start', 0))
    end = int(data.get('end', 999999999999999999))
    file_path = os.path.join(project_name + '/outputs', 'logs.db') # 'projects/cat/outputs/log.txt
    print("File path: ", file_path)

    logs = read_logs(file_path, start, end)
    print("Logs: ", logs)
    return jsonify(logs)

@app.route('/download', methods=['POST'])
def request_download():
    # save the project, convert it to a zip file, save it to the projects directory, and return the path
    data = request.get_json()
    project_name = data['project']
    return download_project(project_name)


@app.route('/get_files', methods=['POST'])
def request_files():

    try:

        data = request.get_json()


        project_name = data['project']
        files = get_files(project_name)

        return jsonify(files)

    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_file', methods=['POST'])
def request_file():
    try:
        data = request.get_json()
        if 'file' not in data:
            raise KeyError("The key 'file' is not present in the JSON payload.")
        
        project_name = data['project']
        file = data['file']
        return get_file(project_name, file)
    
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/upload_file', methods=['POST'])
def request_upload_file():
    try:
        data = request.get_json()
        if 'file' not in data:
            raise KeyError("The key 'file' is not present in the JSON payload.")
        if 'content' not in data:
            raise KeyError("The key 'content' is not present in the JSON payload.")

        file = data['file']
        content = data['content']
        project_name = data['project']
        return upload_file(project_name, file, content)
    
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/execute', methods=['POST'])
async def request_execute():
    data = request.get_json()
    project_name = data['project']
    output = data['output']  # 'log' and/or 'image' and/or 'video'
    duration = data['duration']
    print(project_name, output, duration)
    result = await execute_project(project_name, outputs=output, duration=duration)
    print(result)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
