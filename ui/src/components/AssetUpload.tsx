import { useCallback, useRef, useState } from "react";
import { s, tokens } from "../styles";

interface AssetUploadProps {
  onUpload: (args: { filename: string; base64_data: string }) => Promise<void>;
  onAfterUpload?: () => void | Promise<void>;
  compact?: boolean;
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const idx = result.indexOf(",");
      resolve(idx >= 0 ? result.slice(idx + 1) : result);
    };
    reader.onerror = () => reject(reader.error || new Error("read failed"));
    reader.readAsDataURL(file);
  });
}

export function AssetUpload({ onUpload, onAfterUpload, compact }: AssetUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      if (list.length === 0) return;
      setBusy(true);
      setError("");
      try {
        for (const file of list) {
          const base64 = await fileToBase64(file);
          await onUpload({ filename: file.name, base64_data: base64 });
        }
        if (onAfterUpload) await onAfterUpload();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setBusy(false);
      }
    },
    [onUpload, onAfterUpload],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files.length) void uploadFiles(e.dataTransfer.files);
      }}
      style={{
        border: `2px dashed ${isDragging ? tokens.ring : tokens.borderPrimary}`,
        borderRadius: tokens.radiusSm,
        background: isDragging ? tokens.bgTertiary : "transparent",
        padding: compact ? "0.85rem" : "1.25rem",
        textAlign: "center",
        cursor: busy ? "progress" : "pointer",
        transition: "background 120ms ease, border-color 120ms ease",
        color: tokens.textSecondary,
        fontSize: tokens.textSm,
        lineHeight: tokens.textSmLh,
      }}
      onClick={() => !busy && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Upload assets"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        style={{ display: "none" }}
        onChange={(e) => {
          if (e.target.files) void uploadFiles(e.target.files);
          e.target.value = "";
        }}
      />
      {busy ? (
        <span>Uploading…</span>
      ) : (
        <>
          <div style={{ fontWeight: tokens.weightSemibold, color: tokens.textPrimary }}>
            Drop files here
          </div>
          <div style={{ marginTop: "0.2rem" }}>
            or <span style={{ color: tokens.textAccent }}>browse</span>
          </div>
        </>
      )}
      {error && (
        <div style={{ marginTop: "0.5rem", color: tokens.danger, fontSize: tokens.textXs }}>
          {error}
        </div>
      )}
      <button style={{ ...s.btn, ...s.btnPrimary, marginTop: "0.75rem", display: "none" }}>
        Upload
      </button>
    </div>
  );
}
