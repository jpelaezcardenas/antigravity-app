const fs = require('fs');
const PDFParser = require("pdf2json");

const pdfParser = new PDFParser(this, 1);

pdfParser.on("pdfParser_dataError", errData => console.error(errData.parserError) );
pdfParser.on("pdfParser_dataReady", pdfData => {
    fs.writeFileSync("extracted_kb.txt", pdfParser.getRawTextContent());
    console.log("PDF extraction successful.");
});

pdfParser.loadPDF("Base de conocimientos-Contexia (2).pdf");
