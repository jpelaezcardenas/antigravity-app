"use client";

import { useRef, useState } from "react";
import { uploadDataFile, type IngestionResult } from "@/lib/ingestion-api";

type UploadState = "idle" | "uploading" | "success" | "error";

const ACCEPTED_FORMATS = ".csv,.xlsx,.xls,.xml,.pdf";

const FORMAT_LABELS: Record<string, string> = {
  ".csv": "CSV Siigo",
  ".xlsx": "Excel",
  ".xls": "Excel",
  ".xml": "XML DIAN",
  ".pdf": "Factura PDF",
};

function getFormatLabel(filename: string): string {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf("."));
  return FORMAT_LABELS[ext] ?? "Archivo";
}

export function DataUploadCard() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [fileName, setFileName] = useState<string>("");

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setState("uploading");
    setResult(null);

    const res = await uploadDataFile(file, true);
    setResult(res);
    setState(res.success ? "success" : "error");

    // Reset input so the same file can be re-uploaded after an error
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleButtonClick() {
    inputRef.current?.click();
  }

  function handleReset() {
    setState("idle");
    setResult(null);
    setFileName("");
  }

  return (
    <div className="rounded-2xl border border-[#1e293b] bg-[#0f172a] p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[14px] font-semibold text-[#f8fafc]">Conectar mis datos</h3>
          <p className="text-[12px] text-[#94a3b8] mt-0.5">
            Sube un CSV de Siigo, Excel, XML DIAN o factura PDF
          </p>
        </div>
        <span className="text-[20px]">📂</span>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_FORMATS}
        className="hidden"
        onChange={handleFileChange}
        aria-label="Seleccionar archivo para subir"
      />

      {state === "idle" && (
        <button
          onClick={handleButtonClick}
          className="w-full rounded-xl border border-[#2DD4BF]/30 bg-[#2DD4BF]/10 px-4 py-3 text-[13px] font-medium text-[#2DD4BF] hover:bg-[#2DD4BF]/20 transition-colors"
        >
          Seleccionar archivo
        </button>
      )}

      {state === "uploading" && (
        <div className="flex items-center gap-3 rounded-xl bg-[#1e293b] px-4 py-3">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#2DD4BF] border-t-transparent" />
          <span className="text-[13px] text-[#94a3b8]">
            Procesando {getFormatLabel(fileName)}&hellip;
          </span>
        </div>
      )}

      {state === "success" && result && (
        <div className="rounded-xl bg-emerald-950/40 border border-emerald-700/30 px-4 py-3 flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 text-[16px]">✓</span>
            <span className="text-[13px] font-medium text-emerald-300">
              {result.row_count} transacciones importadas
            </span>
          </div>
          {result.date_range && (
            <p className="text-[12px] text-emerald-600 ml-6">{result.date_range}</p>
          )}
          <button
            onClick={handleReset}
            className="mt-2 ml-6 text-[12px] text-[#94a3b8] underline hover:text-[#f8fafc]"
          >
            Subir otro archivo
          </button>
        </div>
      )}

      {state === "error" && result && (
        <div className="rounded-xl bg-red-950/40 border border-red-700/30 px-4 py-3 flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-red-400 text-[16px]">✗</span>
            <span className="text-[13px] font-medium text-red-300">Error al importar</span>
          </div>
          <p className="text-[12px] text-red-600 ml-6">{result.error}</p>
          <button
            onClick={handleReset}
            className="mt-2 ml-6 text-[12px] text-[#94a3b8] underline hover:text-[#f8fafc]"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      <p className="text-[11px] text-[#475569]">
        Formatos aceptados: CSV Siigo · Excel · XML DIAN · Factura PDF
      </p>
    </div>
  );
}
