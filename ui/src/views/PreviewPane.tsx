import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";
import { PDFViewer } from "../components/PDFViewer";
import { useExport } from "../hooks/useExport";

interface PreviewPaneProps {
  blob: Blob | null;
  loading: boolean;
  error: string;
  hasSelection: boolean;
  emptyHint: string;
}

export function PreviewPane({
  blob,
  loading,
  error,
  hasSelection,
  emptyHint,
}: PreviewPaneProps) {
  const { t } = useThemeTokens();
  const { exportPdf } = useExport();

  return (
    <div
      className="collateral-preview-pane"
      style={{ ...s.rightPanel, background: t("background", "#ffffff") }}
    >
      {blob ? (
        <PDFViewer blob={blob} onDownload={exportPdf} />
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
