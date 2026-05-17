#!/usr/bin/env node

/**
 * Generar iconos PWA desde SVG (usando Sharp)
 * Esto crea los 4 iconos con el diseño de Contexia
 */

const sharp = require("sharp");
const path = require("path");
const fs = require("fs");

const ICON_SIZES = [192, 512];

// SVG del logo de Contexia (versión simplificada)
const CONTEXIA_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#a1ff00;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#00ff88;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0099ff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- Fondo transparente -->
  <!-- Círculo gradiente -->
  <circle cx="100" cy="100" r="95" fill="url(#grad1)" opacity="0.3" stroke="url(#grad1)" stroke-width="8"/>

  <!-- Barras de gráfico -->
  <rect x="70" y="110" width="12" height="30" fill="#a1ff00"/>
  <rect x="88" y="100" width="12" height="40" fill="#ffff00"/>
  <rect x="106" y="85" width="12" height="55" fill="#00ff88"/>

  <!-- Punto de datos -->
  <circle cx="60" cy="95" r="6" fill="white"/>

  <!-- Línea de trend -->
  <path d="M 60 95 Q 85 80 115 85" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round"/>
  <circle cx="85" cy="82" r="3" fill="white"/>
  <circle cx="100" cy="84" r="3" fill="white"/>

  <!-- Flecha -->
  <path d="M 130 100 L 145 85 M 145 85 L 145 100 M 145 85 L 130 85" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Checkmark/Pin base -->
  <path d="M 100 145 L 85 160 L 70 145" stroke="url(#grad1)" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
`;

async function generateIcon(size, isMaskable = false) {
  try {
    const iconsDir = path.join(__dirname, "../public/icons");
    if (!fs.existsSync(iconsDir)) {
      fs.mkdirSync(iconsDir, { recursive: true });
    }

    const suffix = isMaskable ? "-maskable" : "";
    const filename = `icon-${size}x${size}${suffix}.png`;
    const outputPath = path.join(iconsDir, filename);

    // Para maskable, usamos más espacio (logo más grande)
    const padding = isMaskable ? Math.floor(size * 0.08) : Math.floor(size * 0.20);
    const innerSize = size - padding * 2;

    let svg = CONTEXIA_SVG;

    // Crear SVG con padding
    svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#a1ff00;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#00ff88;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0099ff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- Fondo -->
  <rect width="${size}" height="${size}" fill="#0a0a0a" rx="0"/>
  <!-- Contenedor centrado -->
  <g transform="translate(${padding}, ${padding}) scale(${innerSize / 200})">
    <circle cx="100" cy="100" r="95" fill="url(#grad1)" opacity="0.3" stroke="url(#grad1)" stroke-width="8"/>
    <rect x="70" y="110" width="12" height="30" fill="#a1ff00"/>
    <rect x="88" y="100" width="12" height="40" fill="#ffff00"/>
    <rect x="106" y="85" width="12" height="55" fill="#00ff88"/>
    <circle cx="60" cy="95" r="6" fill="white"/>
    <path d="M 60 95 Q 85 80 115 85" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round"/>
    <circle cx="85" cy="82" r="3" fill="white"/>
    <circle cx="100" cy="84" r="3" fill="white"/>
    <path d="M 130 100 L 145 85 M 145 85 L 145 100 M 145 85 L 130 85" stroke="url(#grad1)" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M 100 145 L 85 160 L 70 145" stroke="url(#grad1)" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
    `;

    await sharp(Buffer.from(svg))
      .png()
      .toFile(outputPath);

    console.log(`✓ Generado: ${filename}`);
    return true;
  } catch (err) {
    console.error(`✗ Error generando icon-${size}x${size}: ${err.message}`);
    return false;
  }
}

async function main() {
  console.log("📦 Generador de Iconos PWA - Contexia\n");

  let success = true;

  // Generar normales
  console.log("Generando iconos normales...");
  for (const size of ICON_SIZES) {
    const result = await generateIcon(size, false);
    success = success && result;
  }

  console.log("\nGenerando iconos maskable...");
  // Generar maskable
  for (const size of ICON_SIZES) {
    const result = await generateIcon(size, true);
    success = success && result;
  }

  if (success) {
    console.log("\n✅ Todos los iconos generados en public/icons/");
  } else {
    console.log("\n⚠️ Algunos iconos fallaron");
    process.exit(1);
  }
}

main();
