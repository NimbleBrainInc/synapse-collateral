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

/**
 * Map a raw Typst compile error to a one-line hint end users can act on.
 * Falls back to a generic message when no pattern matches.
 */
function friendlyHint(raw: string): string {
  const lower = raw.toLowerCase();
  if (lower.includes("failed to decode image")) {
    return "An image in this document is corrupt or can't be read. Re-upload the asset.";
  }
  if (lower.includes("file not found")) {
    return "A file this document references is missing. Check asset names.";
  }
  if (lower.includes("unknown font family")) {
    return "A font this document uses isn't installed. Install it, or change the font.";
  }
  if (lower.includes("unknown variable") || lower.includes("unknown ident")) {
    return "The document references something that isn't defined.";
  }
  if (lower.includes("expected ")) {
    return "There's a syntax error in the document source.";
  }
  return "There's a problem with the document source.";
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
            <div
              style={{
                maxWidth: "520px",
                width: "100%",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                textAlign: "left",
              }}
            >
              <div
                style={{
                  fontFamily: tokens.fontHeading,
                  fontSize: tokens.headingSm,
                  fontWeight: tokens.weightSemibold,
                  color: tokens.textPrimary,
                  lineHeight: tokens.headingSmLh,
                }}
              >
                Couldn't render preview
              </div>
              <div
                style={{
                  fontSize: tokens.textSm,
                  color: tokens.textSecondary,
                  lineHeight: tokens.textSmLh,
                }}
              >
                {friendlyHint(error)}
              </div>
              <details style={{ marginTop: "0.25rem" }}>
                <summary
                  style={{
                    fontSize: tokens.textSm,
                    color: tokens.textSecondary,
                    cursor: "pointer",
                    userSelect: "none",
                    padding: "0.25rem 0",
                  }}
                >
                  Show technical details
                </summary>
                <pre
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.75rem",
                    background: tokens.bgSecondary,
                    border: `1px solid ${tokens.borderPrimary}`,
                    borderRadius: tokens.radiusSm,
                    color: tokens.textPrimary,
                    fontFamily: tokens.fontMono,
                    fontSize: "12px",
                    lineHeight: 1.45,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    maxHeight: "320px",
                    overflow: "auto",
                    margin: 0,
                  }}
                >
                  {error}
                </pre>
              </details>
            </div>
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
