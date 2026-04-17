import { useEffect, useMemo, useState } from "react";
import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";
import { PDFViewer } from "../components/PDFViewer";

interface PreviewPaneProps {
  title: string;
  blob: Blob | null;
  loading: boolean;
  error: string;
  hasSelection: boolean;
  emptyHint: string;
}

export function PreviewPane({
  title,
  blob,
  loading,
  error,
  hasSelection,
  emptyHint,
}: PreviewPaneProps) {
  const { t } = useThemeTokens();

  // Keep a blob URL solely for the header "Download" link. The PDFViewer
  // rasterizes internally and does not need a blob URL.
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!blob) {
      setDownloadUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }
    const url = URL.createObjectURL(blob);
    setDownloadUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [blob]);

  const downloadFilename = useMemo(() => {
    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return `${slug || "document"}.pdf`;
  }, [title]);

  return (
    <div
      className="collateral-preview-pane"
      style={{ ...s.rightPanel, background: t("secondary", "#f3f4f6") }}
    >
      <div
        className="collateral-preview-frame"
        style={{
          ...s.previewFrame,
          background: t("background", "#ffffff"),
          borderColor: t("border", "#e5e7eb"),
        }}
      >
        <div
          style={{
            ...s.previewHeader,
            borderBottomColor: t("border", "#e5e7eb"),
            color: t("muted", "#6b7280"),
          }}
        >
          <div style={s.previewHeaderLabel}>
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M14 3v4a1 1 0 0 0 1 1h4" />
              <path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" />
            </svg>
            <span style={s.previewHeaderName}>{title}</span>
          </div>
          {downloadUrl && (
            <a
              href={downloadUrl}
              download={downloadFilename}
              aria-label="Download PDF"
              style={{ ...s.previewDownload, color: t("muted", "#6b7280") }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 3v12" />
                <path d="m7 10 5 5 5-5" />
                <path d="M5 21h14" />
              </svg>
            </a>
          )}
        </div>
        <div style={s.previewBody}>
          {blob ? (
            <PDFViewer blob={blob} />
          ) : (
            <div style={{ ...s.previewStatus, color: t("muted", "#6b7280") }}>
              {error ? (
                <span style={{ color: t("destructive", "#ef4444") }}>{error}</span>
              ) : loading ? (
                <span className="collateral-preview-dots" aria-label="Rendering">
                  Rendering<span>.</span>
                  <span>.</span>
                  <span>.</span>
                </span>
              ) : !hasSelection ? (
                <span>{emptyHint}</span>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
