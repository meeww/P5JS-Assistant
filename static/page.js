let chat_log = [];
let files = []
let current_file = "";

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

    // Recursive function to create the list elements
    function createList(items, currentPath) {
        const ul = document.createElement('ul');

        items.forEach(item => {
            const li = document.createElement('li');

            if (typeof item === 'string') {
                li.textContent = item;
                li.classList.add('file');
                const filePath = currentPath ? `${currentPath}/${item}` : item;
                li.addEventListener('click', () => getFile(filePath));
            } else if (typeof item === 'object') {
                const key = Object.keys(item)[0];
                li.textContent = `${key}/`;
                li.classList.add('directory');
                li.appendChild(createList(item[key], currentPath ? `${currentPath}/${key}` : key));
            }

            ul.appendChild(li);
        });

        return ul;
    }

    // Create and append the directory structure to the container
    const directoryList = createList(structure, parentPath);
    container.appendChild(directoryList);
}


function getFiles(){
    fetch('/get_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project: project_name })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        files = data;
        updateDirectory(data);  

        file = files[0];
        getFile(file);
        
        
        
    })
    .catch(error => console.error('Error getting files:', error));
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
        current_file = filename;
    })
    .catch(error => console.error('Error getting file:', error));
}

function getLogs(){
    fetch('/logs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ start: 0, end: 999999999999999999})
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        updateLog(data);
    })
    .catch(error => {
        console.error('Error fetching logs:', error);
    });
}

function updateLog(logs){

    chat_log = [];
    for (line of logs){
        chat_log.push(line);
    }


    log.scrollTop = log.scrollBottom;
    log.style.display = "block";
    let parent = log.parentElement;
    showControlOverlay(parent);
    renderVirtualScroll();
}

function updateImage(data){

    let image = document.getElementById("image");
    image.src = '/projects/'+project_name+'/outputs/'+data['image']+'?t='+new Date().getTime();
    image.style.display = "block";
    let parent = image.parentElement;
    showControlOverlay(parent);
}

function updateVideo(data){
    let video = document.getElementById("video");
    video.src = '/projects/'+project_name+'/outputs/'+data['video']+'?t='+new Date().getTime();
    video.style.display = "block";
    let parent = video.parentElement;
    showControlOverlay(parent);
}


function updateIFrame(project_name) {
    let iframe = document.getElementById("iframe");

    
    // Update the iframe src to force reload and bypass caching
    iframe.src = '/projects/'+project_name+'/src/index.html?t='+new Date().getTime();
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
    let filename = current_file.split('/').pop();
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
    // upload the file to the server
    let textarea = document.getElementById("code");
    let text = textarea.value;


    fetch('/upload_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project: project_name, file: current_file, content: text })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => console.error('Error uploading file:', error));
});