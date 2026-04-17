import { s, tokens } from "../styles";
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
  const { exportPdf } = useExport();

  return (
    <div className="collateral-preview-pane" style={s.rightPanel}>
      {blob ? (
        <PDFViewer blob={blob} onDownload={exportPdf} />
      ) : (
        <div style={s.previewStatus}>
          {error ? (
            <span style={{ color: tokens.danger }}>{error}</span>
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
