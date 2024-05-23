


console.log('Hello World!');
console.log('This is a silly project just to test an automatic code executor.');
console.log('The code executor will run the code in the backend and return the output to the frontend.');
console.log('The output can be text, image, or video.');
console.log('Let\'s see what the code executor will return for this project.');

for (let i = 0; i < 100; i++) {
    console.log(i+1 + ' Meow!');
}

// set random background color

let hue = Math.random() * 360;
document.body.style.backgroundColor = 'hsl(' + Math.random() * 360 + ', 100%, 75%)';
// animate the background color
setInterval(() => {
    // every one frame, very slightly change the hue
    document.body.style.backgroundColor = 'hsl(' + (hue += 0.1) + ', 100%, 75%)';
}, 1000 / 60);

