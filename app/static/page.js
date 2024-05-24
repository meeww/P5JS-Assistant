let chat_log = [];
let files = []
let current_file = "";
let original_content = "";




function hideElements(ids){
    ids.forEach(id => {
        if(document.getElementById(id)){
            document.getElementById(id).style.display = "none";
        }
        if(document.getElementsByClassName(id)){
            let elements = document.getElementsByClassName(id);
            for (element of elements){
                element.style.display = "none";
            }
        }
    });
}


function updateDirectory(structure, parentPath = '') {
    const container = document.getElementById('directory_list');
    container.innerHTML = ''; // Clear any existing content

    // append the project name to the top of the list
    structure = { [project_name]: structure };

    function createList(items, currentPath = '', depth = 0) {
        const ul = document.createElement('ul');

        for (const key in items) {
            const li = document.createElement('li');
            const buttonContainer = document.createElement('div');
            buttonContainer.classList.add('button-container');
            const deleteButton = document.createElement('button');
            deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
            deleteButton.classList.add('delete-button');
            deleteButton.title = 'Delete';

            const label = document.createElement('label');
            // if key is a directory, append a '/' to the end
            if (typeof items[key] !== 'string') {
                label.textContent = key + '/';
                const newFileButton = document.createElement('button');
                newFileButton.innerHTML = '<i class="fas fa-plus"></i>';
                newFileButton.classList.add('new-file-button');
                newFileButton.title = 'New File';
                newFileButton.addEventListener('click', () => {
                    const newFileName = prompt('Enter the name of the new file:', 'new_file.txt');
                    if (newFileName) {
                        console.log(newFileName, key);
                        const newFilePath = key + '/' + newFileName;
                        fetch('/create_file', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ project_name: project_name, file: newFilePath })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('New file created successfully');
                                // Reload the directory structure after creating the new file
                                getFiles();
                            } else {
                                alert('Error creating new file: ' + data.error);
                            }
                        })
                        .catch(error => console.error('Error creating new file:', error));
                    }
                }
                );
                buttonContainer.appendChild(newFileButton);
                

            }
            else{
                label.textContent = key;
            }
            label.htmlFor = key;
            label.style.marginLeft = `${depth * 20}px`;
            label.style.width = `calc(100% - ${depth * 20}px)`;

            const fullPath = currentPath ? `${currentPath}/${key}` : key;

           
            li.appendChild(label);
            buttonContainer.appendChild(deleteButton);
            label.appendChild(buttonContainer);
            if (typeof items[key] === 'string') {
                li.classList.add('file');
                li.addEventListener('click', () => getFile(fullPath));
                deleteButton.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent triggering the file click event
                    deleteFile(fullPath);
                });
            } else {
                li.classList.add('directory');
                const nestedUl = createList(items[key], fullPath, depth + 1);
                li.appendChild(nestedUl);
                deleteButton.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent triggering the directory click event
                    deleteFile(fullPath);
                });
            }

            ul.appendChild(li);
        }

        return ul;
    }

    const directoryList = createList(structure);
    container.appendChild(directoryList);
}


function deleteFile(filePath) {
    if (confirm(`Are you sure you want to delete ${filePath}?`)) {
        fetch('/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_name: project_name, file: filePath })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('File deleted successfully');
                // Reload the directory structure after deletion
                getFiles();
                
            } else {
                alert('Error deleting file: ' + data.error);
            }
        })
        .catch(error => console.error('Error deleting file:', error));
    }
}

function findFirstFile(structure, path = '') {
    for (const key in structure) {
        const newPath = path ? `${path}/${key}` : key;
        if (typeof structure[key] === 'string') {
            return newPath;
        } else {
            const result = findFirstFile(structure[key], newPath);
            if (result) return result;
        }
    }
    return null;
}


async function getFiles() {
    try {
        const response = await fetch('/get_files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_name: project_name })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        updateDirectory(data);
    } catch (error) {
        console.error('Error getting files:', error);
    }
}
async function fetchLogs() {
    try {
        const response = await fetch('/logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_name: project_name })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        updateLog(data);
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

function getFile(filename) {
    console.log(filename);
    fetch('/get_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project: project_name, file: filename })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        let textarea = document.getElementById("code");
        textarea.value = data['content'];
        original_content = data['content'];

        current_file = filename;

        // show the control overlay
        let parent = textarea.parentElement;
        showControlOverlay(parent);
        compareContent();
    })
    .catch(error => console.error('Error getting file:', error));
}

function compareContent() {
    let newcode = document.getElementById("code").value;
    let oldcode = original_content;

    const diff = Diff.diffChars(oldcode, newcode);
    const display = document.getElementById('diff-output');
    
    // Clear the previous content
    display.innerHTML = '';

    // Concatenate the differences into a single string with HTML styling

    
    let diffHtml = '';
    diff.forEach((part) => {
        // green for additions, red for deletions, grey for common parts
        const color = part.added ? 'lime' : part.removed ? 'red' : 'var(--accent-color)'
        const text = part.value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        diffHtml += `<span style="color: ${color}">${text}</span>`;
    });

    // Create a pre element to preserve whitespace and formatting
    const pre = document.createElement('pre');
    pre.innerHTML = diffHtml;

    // Append the pre element to the display
    display.appendChild(pre);

    // Show the diff output
    display.style.display = 'block';
}



async function getLogs(){
    try {
        const response = await fetch('/logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_name: project_name })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        updateLog(data);
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

function updateLog(logs){
    try {
        chat_log = [];
        for (line of logs){
            chat_log.push(line);
        }


        log.scrollTop = log.scrollBottom;
        log.style.display = "block";
        let parent = log.parentElement;
        showControlOverlay(parent);
        renderVirtualScroll();
    } catch (error) {
        console.error('Error updating log:', error);
    }
}

function updateImage(data) {
    let image = document.getElementById("image");
    image.src = `/projects/${user_id}/${project_name}/outputs/${data['image']}?t=${new Date().getTime()}`;
    image.style.display = "block";
    let parent = image.parentElement;
    showControlOverlay(parent);
}

function updateVideo(data) {
    let video = document.getElementById("video");
    video.src = `/projects/${user_id}/${project_name}/outputs/${data['video']}?t=${new Date().getTime()}`;
    video.style.display = "block";
    let parent = video.parentElement;
    showControlOverlay(parent);
}

function updateIFrame(project_name) {
    let iframe = document.getElementById("iframe");
    
    // Update the iframe src to force reload and bypass caching
    iframe.src = `/projects/${user_id}/${project_name}/src/index.html?t=${new Date().getTime()}`;
    iframe.style.display = "block";

    // Show the control overlay
    let parent = iframe.parentElement;
    showControlOverlay(parent);
}



function showControlOverlay(parent){
    let control_overlay = parent.getElementsByClassName("control_overlay")[0];
    control_overlay.style.display = "flex";

}

hideElements(['log', 'image', 'video', 'iframe']);


getFiles(project_name);

getLogs();
updateIFrame(project_name);
updateImage({image: "image.png"});
updateVideo({video: "video.webm"});


document.getElementById('form').addEventListener('submit', function(event) {
    event.preventDefault();
    // delete the log old elements
    hideElements(['log', 'image', 'video', 'iframe','control_overlay']);
    // display the spinner
    document.getElementById('spinner').style.display = "block";

    outputs = [];
    if(document.getElementById('log_checkbox').checked){
        outputs.push('log');
    }
    if(document.getElementById('image_checkbox').checked){  
        outputs.push('image');
    }
    if(document.getElementById('video_checkbox').checked){
        outputs.push('video');
    }
    if(document.getElementById('iframe_checkbox').checked){
        outputs.push('url');
    }


    // Fetch the execution data from the backend (app.py)
    fetch('/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({project : project_name, output: outputs, duration: 1})
    })
    .then(response => response.json())
    .then(data => {
        // hide the spinner
        document.getElementById('spinner').style.display = "none";
        // Handle the response data
        if(data['log']) {
            // load the logs from the static/logs.db file
            try{
                fetch('projects/' + project_name + '/logs.db')
                .then(response => response.text())
                .then(data => {
                    getLogs();
                });
            }

            catch (error){
                console.error('Error getting logs:', error);
            }

        }
        if(data['image']) {
            updateImage(data);
        }
        if(data['video']) {
            updateVideo(data);
        }
        if(data['url']) {
            updateIFrame(project_name);
        }

        
    });
    
});
console.log("Page.js loaded!")

let popupTimeout = null;
// handle small popups
function popup(message) {
    const popup = document.getElementById('popup');
    
    // Clear the previous timeout if it exists
    if (popupTimeout) {
        clearTimeout(popupTimeout);
        popupTimeout = null;
    }

    // Remove any previous animations
    popup.style.animation = 'none';
    
    // Force a reflow to reset the animation
    popup.offsetHeight;
    
    // Apply the show class and animations
    popup.textContent = message;
    popup.style.left = event.clientX + 'px';
    popup.style.top = event.clientY + 'px';
    popup.classList.add('show');
    popup.style.animation = 'popOpen 0.5s ease-in-out forwards';

    // Set a new timeout for hiding the popup
    popupTimeout = setTimeout(() => {
        popup.style.animation = 'popClose 0.5s ease-in-out forwards';
        popupTimeout = setTimeout(() => {
            popup.classList.remove('show');
        }, 500); // Duration of the popClose animation
    }, 3000); // Display for 3 seconds
}


// handle <a> clicks

document.getElementById('download_image').addEventListener('click', function(event) {

    // download the image
    let image = document.getElementById("image");
    let link = document.createElement('a');
    link.href
    link.href = image.src;
    link.download = 'image.png';
    link.click();
});

document.getElementById('copy_image').addEventListener('click', function(event) {
    // copy the image to the clipboard
    let image = document.getElementById("image");
    let canvas = document.createElement('canvas');
    // get actual size of the image
    canvas.width = 512;
    canvas.height = 512;

    let ctx = canvas.getContext('2d');
    ctx.drawImage(image, 0, 0);
    canvas.toBlob(blob => {
        navigator.clipboard.write([
            new ClipboardItem({
                'image/png': blob
            })
        ]);
    });
    

    popup("Image URL copied to clipboard");
}
);

document.getElementById('open_image').addEventListener('click', function(event) {
    // open the image in a new tab
    let image = document.getElementById("image");
    window.open(image.src, '_blank');
});

document.getElementById('download_video').addEventListener('click', function(event) {
    // download the video
    let video = document.getElementById("video");
    let link = document.createElement('a');
    link.href = video.src;
    link.download = 'video.webm';
    link.click();
});

document.getElementById('copy_video').addEventListener('click', function(event) {
    // copy the video to the clipboard
    let video = document.getElementById("video");
    navigator.clipboard.writeText(video.src);
    popup("Video URL copied to clipboard");
});

document.getElementById('open_video').addEventListener('click', function(event) {
    // open the video in a new tab
    let video = document.getElementById("video");
    window.open(video.src, '_blank');
});

document.getElementById('download_log').addEventListener('click', function(event) {
    // download the logs as a text file
    let log = document.getElementById("log");
    let text = "";
    for (line of chat_log){
        text += cleanMessage(line) + "\n";
    }
    let link = document.createElement('a');
    let blob = new Blob([text], {type: 'text/plain'});
    link.href = URL.createObjectURL(blob);
    link.download = 'log.txt';
    link.click();
}
);

document.getElementById('copy_log').addEventListener('click', function(event) {
    // copy the logs to the clipboard
    let text = "";
    for (line of chat_log){
        text += cleanMessage(line) + "\n";
    }
    navigator.clipboard.writeText(text);
    popup("Log copied to clipboard");
});

document.getElementById('open_log').addEventListener('click', function(event) {
    // open the logs in a new tab
    let log = document.getElementById("log");
    let text = "";
    for (line of chat_log){
        text += cleanMessage(line) + "\n";
    }
    let blob = new Blob([text], {type: 'text/plain'});
    let url = URL.createObjectURL(blob);
    window.open(url, '_blank');
});

document.getElementById('download_project').addEventListener('click', function(event) {
    // download the project as a zip file
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project: project_name })
    })
    .then(response => response.json())
    .then(data => {
        const downloadLink = document.createElement('a');
        downloadLink.href = `/projects/${project_name}/project.zip`;
        console.log(downloadLink.href);
        downloadLink.download = `${project_name}.zip`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    })
    .catch(error => console.error('Error downloading project:', error));
}
);

document.getElementById('copy_project_url').addEventListener('click', function(event) {
    // copy the project url to the clipboard
    navigator.clipboard.writeText(window.location.href+"/projects/"+project_name+"/index.html");
    popup("Project URL copied to clipboard");
});

document.getElementById('open_project').addEventListener('click', function(event) {
    // open the project in a new tab
    window.open(window.location.href+"/projects/"+project_name+"/index.html", '_blank');
});

document.getElementById('download_file').addEventListener('click', function(event) {
    // download the file
    let textarea = document.getElementById("code");
    let text = textarea.value;
    let link = document.createElement('a');
    let filename = current_file.split("\\").pop();
    let filetype = filename.split('.').pop();


    // create a blob from the text as a filetype
    let blob = new Blob([text], {type: 'text/'+filetype});
    link.href = URL.createObjectURL(blob);
    link.download = filename;

    link.click();
});

document.getElementById('open_file').addEventListener('click', function(event) {
    // open the file in a new tab
    let textarea = document.getElementById("code");
    let text = textarea.value;
    let blob = new Blob([text], {type: 'text/plain'});
    let url = URL.createObjectURL(blob);
    window.open(url, '_blank');
});

document.getElementById('copy_file').addEventListener('click', function(event) {
    // copy the file to the clipboard
    let textarea = document.getElementById("code");
    navigator.clipboard.writeText(textarea.value);
    popup("File copied to clipboard");
});

document.getElementById('upload_file').addEventListener('click', function(event) {
    // Upload the file to the server
    let textarea = document.getElementById("code");
    let text = textarea.value;

    // Ensure project_name and current_file are defined

    fetch('/upload_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project_name: project_name, file: current_file, content: text })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => console.error('Error uploading file:', error));
});

const socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('file_change', function(data) {
    console.log(data.message);
    getFiles();  // Refresh the file list
});
