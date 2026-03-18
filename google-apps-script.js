/**
 * INSTRUCCIONES DE CONFIGURACIÓN:
 * 
 * 1. Ve a https://script.google.com/
 * 2. Inicia sesión con jpelaezcardenas@gmail.com
 * 3. Crea un nuevo proyecto (+ New Project)
 * 4. Borra el contenido y pega TODO este código
 * 5. Guarda el proyecto (Ctrl+S) y dale un nombre como "Contexia Entrevistas"
 * 6. Click en "Deploy" > "New Deployment"
 * 7. En tipo, selecciona "Web app"
 * 8. Configura:
 *    - Description: "Contexia Interview Collector"
 *    - Execute as: "Me (jpelaezcardenas@gmail.com)"
 *    - Who has access: "Anyone"
 * 9. Click "Deploy"
 * 10. Copia la URL del deployment y pégala en el landing.html donde dice GOOGLE_APPS_SCRIPT_URL
 */

// Nombre de la hoja de cálculo donde se guardarán las respuestas
const SPREADSHEET_NAME = "Contexia - Respuestas Entrevistas";

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    
    // Buscar o crear la hoja de cálculo
    let spreadsheet = getOrCreateSpreadsheet();
    let sheet = spreadsheet.getActiveSheet();
    
    // Si la hoja está vacía, crear encabezados
    if (sheet.getLastRow() === 0) {
      const headers = [
        "Timestamp",
        "P1 - Proceso de formalización (Texto)",
        "P1 - Proceso de formalización (Audio Transcrito)",
        "P2 - Miedo DIAN/Cámara Comercio (Texto)",
        "P2 - Miedo DIAN/Cámara Comercio (Audio Transcrito)",
        "P3 - Error tributario (Texto)",
        "P3 - Error tributario (Audio Transcrito)",
        "P4 - Tiempo y dinero en trámites (Texto)",
        "P4 - Tiempo y dinero en trámites (Audio Transcrito)",
        "P5 - Herramientas contables (Texto)",
        "P5 - Herramientas contables (Audio Transcrito)",
        "P6 - Robot guía fiscal (Texto)",
        "P6 - Robot guía fiscal (Audio Transcrito)",
        "P7 - Disposición a pagar (Texto)",
        "P7 - Disposición a pagar (Audio Transcrito)",
        "P8 - Peor pesadilla fiscal (Texto)",
        "P8 - Peor pesadilla fiscal (Audio Transcrito)",
        "P9 - Consejo a emprendedores (Texto)",
        "P9 - Consejo a emprendedores (Audio Transcrito)",
        "P10 - Comentario final (Texto)",
        "P10 - Comentario final (Audio Transcrito)"
      ];
      sheet.appendRow(headers);
      
      // Formatear encabezados
      const headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#1a1a2e");
      headerRange.setFontColor("#ffffff");
      sheet.setFrozenRows(1);
    }
    
    // Construir fila de datos
    const row = [new Date().toLocaleString("es-CO", { timeZone: "America/Bogota" })];
    
    for (let i = 1; i <= 10; i++) {
      row.push(data[`q${i}_text`] || "");
      row.push(data[`q${i}_audio_transcript`] || "");
    }
    
    // Agregar fila
    sheet.appendRow(row);
    
    // Auto-ajustar columnas
    sheet.autoResizeColumns(1, sheet.getLastColumn());
    
    // Crear también un documento de Google Docs con el resumen
    createDocSummary(data, spreadsheet);
    
    return ContentService
      .createTextOutput(JSON.stringify({ 
        success: true, 
        message: "Respuestas guardadas exitosamente",
        sheetUrl: spreadsheet.getUrl()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ 
        success: false, 
        error: error.toString() 
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({ 
      status: "ok", 
      message: "Contexia Interview Collector is running" 
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateSpreadsheet() {
  const files = DriveApp.getFilesByName(SPREADSHEET_NAME);
  
  if (files.hasNext()) {
    const file = files.next();
    return SpreadsheetApp.openById(file.getId());
  }
  
  // Crear nueva hoja de cálculo
  const spreadsheet = SpreadsheetApp.create(SPREADSHEET_NAME);
  spreadsheet.getActiveSheet().setName("Respuestas");
  
  return spreadsheet;
}

function createDocSummary(data, spreadsheet) {
  const docName = `Contexia - Entrevista ${new Date().toLocaleString("es-CO", { timeZone: "America/Bogota" })}`;
  const doc = DocumentApp.create(docName);
  const body = doc.getBody();
  
  // Título
  body.appendParagraph("Contexia - Entrevista Rápida")
    .setHeading(DocumentApp.ParagraphHeading.HEADING1);
  
  body.appendParagraph(`Fecha: ${new Date().toLocaleString("es-CO", { timeZone: "America/Bogota" })}`)
    .setForegroundColor("#666666");
  
  body.appendParagraph(""); // Línea en blanco
  
  const questions = [
    "Cuéntame cómo fue tu proceso de formalizar tu emprendimiento: ¿qué pasos seguiste y en qué momento te sentiste perdido?",
    "¿Qué fue lo que más te asustó al pensar en la DIAN o en la Cámara de Comercio cuando empezaste?",
    "Describe una situación específica donde hayas sentido miedo a cometer un error tributario... ¿qué pasó después?",
    "¿Cuánto tiempo y plata has gastado hasta ahora solo en trámites legales o contables? ¿Valió la pena?",
    "¿Qué herramientas o personas usas hoy para llevar tu contabilidad? ¿Son suficientes?",
    "Si tuvieras un robot que te guiara paso a paso en cada obligación fiscal... ¿cómo cambiaría tu día a día?",
    "¿Cuánto estarías dispuesto a pagar mensualmente por tener cero estrés con la DIAN y tus impuestos?",
    "¿Cuál es tu peor pesadilla como emprendedor en temas de impuestos o formalización?",
    "Si pudieras darle un consejo a un emprendedor que recién empieza... ¿qué le dirías sobre los temas legales y tributarios?",
    "¿Hay algo más que quieras contarnos sobre tu experiencia con la DIAN o la formalización de tu negocio?"
  ];
  
  for (let i = 0; i < questions.length; i++) {
    const qNum = i + 1;
    
    body.appendParagraph(`Pregunta ${qNum}`)
      .setHeading(DocumentApp.ParagraphHeading.HEADING2);
    
    body.appendParagraph(questions[i])
      .setItalic(true)
      .setForegroundColor("#444444");
    
    const textResponse = data[`q${qNum}_text`] || "(Sin respuesta escrita)";
    const audioTranscript = data[`q${qNum}_audio_transcript`] || "(Sin grabación de audio)";
    
    body.appendParagraph("📝 Respuesta escrita:").setBold(true);
    body.appendParagraph(textResponse);
    
    body.appendParagraph("🎙️ Transcripción de audio:").setBold(true);
    body.appendParagraph(audioTranscript);
    
    body.appendParagraph(""); // Separador
  }
  
  // Mover el doc a la misma carpeta
  doc.saveAndClose();
  
  // Añadir link al doc en la hoja de cálculo
  const sheet = spreadsheet.getActiveSheet();
  const lastRow = sheet.getLastRow();
  // No agregamos link por ahora para evitar complejidad
}
