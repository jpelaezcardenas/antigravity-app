#!/usr/bin/env node

/**
 * Script para generar iconos PWA desde un logo
 * Requiere: ImageMagick (convert) o Sharp (npm install sharp)
 *
 * Uso:
 *   node scripts/generate-icons.js
 *
 * Busca: assets/logo.svg o assets/logo.png
 * Genera: public/icons/icon-*.png
 */

const fs = require("fs");
const path = require("path");

const ICON_SIZES = [192, 512];
const COLORS = {
  primary: "#57F1DB",
  dark: "#0A0A0A",
};

async function generateWithSharp() {
  try {
    const sharp = require("sharp");
    console.log("✓ Sharp encontrado. Generando iconos...");

    const logoPath = findLogoFile();
    if (!logoPath) {
      throw new Error("No se encontró logo en assets/");
    }

    const iconsDir = path.join(__dirname, "../public/icons");
    if (!fs.existsSync(iconsDir)) {
      fs.mkdirSync(iconsDir, { recursive: true });
    }

    // Generar versiones normales
    for (const size of ICON_SIZES) {
      const outputPath = path.join(iconsDir, `icon-${size}x${size}.png`);
      await sharp(logoPath)
        .resize(size, size, {
          fit: "contain",
          background: { r: 255, g: 255, b: 255, alpha: 0 },
        })
        .png()
        .toFile(outputPath);
      console.log(`✓ Generado: icon-${size}x${size}.png`);
    }

    // Generar versiones maskable (cuadradas con margin)
    for (const size of ICON_SIZES) {
      const outputPath = path.join(iconsDir, `icon-${size}x${size}-maskable.png`);
      const margin = Math.floor(size * 0.15); // 15% margin
      const innerSize = size - margin * 2;

      await sharp(logoPath)
        .resize(innerSize, innerSize, {
          fit: "contain",
          background: { r: 255, g: 255, b: 255, alpha: 0 },
        })
        .extend({
          top: margin,
          bottom: margin,
          left: margin,
          right: margin,
          background: { r: 255, g: 255, b: 255, alpha: 0 },
        })
        .png()
        .toFile(outputPath);
      console.log(`✓ Generado: icon-${size}x${size}-maskable.png`);
    }

    console.log("\n✅ Iconos generados correctamente en public/icons/");
  } catch (err) {
    console.error("❌ Error con Sharp:", err.message);
    console.log("\nInstala Sharp:");
    console.log("  npm install --save-dev sharp");
    process.exit(1);
  }
}

function findLogoFile() {
  const assetsDir = path.join(__dirname, "../assets");
  const candidates = ["logo.svg", "logo.png", "logo-icon.svg", "logo-icon.png"];

  if (fs.existsSync(assetsDir)) {
    for (const file of candidates) {
      const fullPath = path.join(assetsDir, file);
      if (fs.existsSync(fullPath)) {
        console.log(`✓ Logo encontrado: ${file}`);
        return fullPath;
      }
    }
  }

  return null;
}

async function main() {
  const logoPath = findLogoFile();

  if (!logoPath) {
    console.log("⚠️  No se encontró logo en assets/");
    console.log("\nOpciones:");
    console.log("  1. Coloca tu logo en: assets/logo.png o assets/logo.svg");
    console.log("  2. Luego ejecuta: node scripts/generate-icons.js");
    console.log("\nO descarga iconos generados online:");
    console.log("  - favicon.io");
    console.log("  - realfavicongenerator.net");
    console.log("  Luego copia los PNG a: public/icons/");
    process.exit(0);
  }

  console.log("📦 Generador de Iconos PWA para Contexia\n");
  console.log(`📍 Logo encontrado: ${logoPath}\n`);

  try {
    await generateWithSharp();
  } catch (err) {
    console.error("Error:", err.message);
    process.exit(1);
  }
}

main();
