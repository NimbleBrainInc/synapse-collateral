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

  // Blob URL for the PDFViewer's download button; revoked on blob change/unmount.
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
      {blob ? (
        <PDFViewer
          blob={blob}
          downloadUrl={downloadUrl ?? undefined}
          downloadFilename={downloadFilename}
        />
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
  );
}
