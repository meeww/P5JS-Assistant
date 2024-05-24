from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import socketio

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, project_path):
        self.project_path = project_path

    def on_any_event(self, event):
        # Emit an event to the client when any file system event is detected
        socketio.emit('file_change', {'message': 'File system has changed'})

def start_monitoring(project_path):
    event_handler = FileChangeHandler(project_path)
    observer = Observer()
    observer.schedule(event_handler, project_path, recursive=True)
    observer.start()
