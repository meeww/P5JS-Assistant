const logContainer = document.getElementById('log');
const itemHeight = 35; // height of each log line in pixels
const buffer = 0; // number of extra items to render above and below the viewport

function cleanMessage(message) {
    message = message[2]
    message = message.split(" ")
    message.shift()
    message.shift()
    message = message.join(" ")
    message = message.replace(/"/g, "")
    return message
}

function renderVirtualScroll() {
    const containerHeight = logContainer.clientHeight;
    const totalHeight = chat_log.length * itemHeight;
    const scrollTop = logContainer.scrollTop;
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer);
    const endIndex = Math.min(chat_log.length, Math.ceil((scrollTop + containerHeight) / itemHeight) + buffer);

    // Calculate padding for the top and bottom
    const topPadding = startIndex * itemHeight;
    const bottomPadding = totalHeight - (endIndex * itemHeight);

    // Create the visible items
    const visibleItems = chat_log.slice(startIndex, endIndex).map((line, index) => {
        const div = document.createElement('div');
        div.className = 'virtual-scroll';
        div.style.top = `${topPadding + index * itemHeight}px`;
        div.style.height = `${itemHeight}px`;
        div.textContent = cleanMessage(line)

        // Stylize the log line based on the log level
        if(line.includes("SEVERE") || line.includes("ERROR") || line.includes("FATAL") || line.includes("CRITICAL")){
            // add error class
            div.className = "error";
            hasError = true;
            
        }
        else if(line.includes("WARNING")){
            // add warning class
            div.className = "warning";
        }
        else if(line.includes("INFO")){
            // add info class
            div.className = "info";
        }

        // set hover text
        div.title = line;

        // Apply squished effect based on distance from the top
        const itemTop = topPadding + index * itemHeight;
        const distanceFromTop = itemTop - scrollTop;
        if (distanceFromTop < itemHeight) {
            var scale = 1 - (itemHeight+1 - distanceFromTop) / itemHeight+1;
            scale = Math.min(1, scale)

            div.style.transform = `scale(1, ${scale}) translate(0, ${itemHeight * (1 - scale) / 2}px)`;
            div.style.opacity = scale;
        } else {
            div.style.transform = 'scale(1, 1)';
            div.style.opacity = 1;
        }


        
        return div;
    });

    // Clear the container and add the new items
    logContainer.innerHTML = '';
    visibleItems.forEach(item => logContainer.appendChild(item));

    // Add padding elements
    const topPaddingDiv = document.createElement('div');
    topPaddingDiv.style.height = `${topPadding}px`;
    logContainer.prepend(topPaddingDiv);

    const bottomPaddingDiv = document.createElement('div');
    bottomPaddingDiv.style.height = `${bottomPadding}px`;
    logContainer.appendChild(bottomPaddingDiv);
}
// Attach the scroll event
logContainer.addEventListener('scroll', renderVirtualScroll);
