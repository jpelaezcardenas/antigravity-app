const fs = require('fs');
const pdf = require('pdf-parse');

let dataBuffer = fs.readFileSync('Base de conocimientos-Contexia (2).pdf');

pdf(dataBuffer).then(function(data) {
    fs.writeFileSync('extracted_kb.txt', data.text);
    console.log("PDF extraction successful. Extracted characters: " + data.text.length);
}).catch(function(error) {
    console.error("Error reading PDF:", error);
});
