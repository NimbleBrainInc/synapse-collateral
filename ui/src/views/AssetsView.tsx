import { useMemo, useState } from "react";
import { s, tokens } from "../styles";
import { AssetUpload } from "../components/AssetUpload";

interface AssetsViewProps {
  assets: string[];
  onUpload: (args: { filename: string; base64_data: string }) => Promise<void>;
  onDelete: (filename: string) => Promise<void>;
  onRefresh: () => Promise<void>;
}

const IMAGE_EXT = new Set(["png", "jpg", "jpeg", "gif", "webp", "svg", "avif"]);
const PDF_EXT = new Set(["pdf"]);

function extOf(filename: string): string {
  const i = filename.lastIndexOf(".");
  return i >= 0 ? filename.slice(i + 1).toLowerCase() : "";
}

function kindOf(filename: string): "image" | "pdf" | "other" {
  const e = extOf(filename);
  if (IMAGE_EXT.has(e)) return "image";
  if (PDF_EXT.has(e)) return "pdf";
  return "other";
}

export function AssetsView({ assets, onUpload, onDelete, onRefresh }: AssetsViewProps) {
  const [selected, setSelected] = useState<string | null>(null);

  const selectedKind = useMemo(
    () => (selected ? kindOf(selected) : null),
    [selected],
  );

  return (
    <div className="collateral-main-layout" style={s.mainLayout}>
      <div className="collateral-left-panel" style={s.leftPanel}>
        <div style={{ ...s.listHeader, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <AssetUpload
            onUpload={onUpload}
            onAfterUpload={onRefresh}
            compact
          />
        </div>
        <div style={s.listScroll}>
          {assets.map((filename) => {
            const active = selected === filename;
            const kind = kindOf(filename);
            return (
              <div
                key={filename}
                style={{
                  ...s.listItem,
                  ...(active ? s.listItemActive : {}),
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                }}
                onClick={() => setSelected(filename)}
              >
                <div
                  style={{
                    ...s.assetThumb,
                    width: 36,
                    height: 36,
                    flexShrink: 0,
                    fontSize: tokens.textXs,
                  }}
                >
                  {kind === "image" ? "IMG" : kind === "pdf" ? "PDF" : extOf(filename).toUpperCase() || "FILE"}
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div
                    style={{
                      ...s.listItemTitle,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                    title={filename}
                  >
                    {filename}
                  </div>
                  <div style={s.listItemMeta}>{kind}</div>
                </div>
                <button
                  aria-label={`Delete ${filename}`}
                  style={s.btnIcon}
                  onClick={async (e) => {
                    e.stopPropagation();
                    try {
                      await onDelete(filename);
                      if (selected === filename) setSelected(null);
                      await onRefresh();
                    } catch {
                      /* non-critical */
                    }
                  }}
                  title="Delete"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <line x1="5" y1="5" x2="19" y2="19" />
                    <line x1="19" y1="5" x2="5" y2="19" />
                  </svg>
                </button>
              </div>
            );
          })}
          {assets.length === 0 && (
            <div
              style={{
                padding: "1rem",
                fontSize: tokens.textSm,
                color: tokens.textSecondary,
                textAlign: "center",
              }}
            >
              No assets yet. Drop a file above to upload.
            </div>
          )}
        </div>
      </div>

      <div className="collateral-preview-pane" style={s.rightPanel}>
        {!selected ? (
          <div style={s.previewStatus}>
            <span>Select an asset to inspect, or drop files into the left rail to upload.</span>
          </div>
        ) : (
          <div
            style={{
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              padding: "1.25rem",
              gap: "0.75rem",
              overflow: "auto",
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: tokens.fontHeading,
                  fontSize: tokens.headingSm,
                  lineHeight: tokens.headingSmLh,
                  fontWeight: tokens.weightSemibold,
                  color: tokens.textPrimary,
                  letterSpacing: "-0.01em",
                }}
              >
                {selected}
              </div>
              <div style={{ ...s.listItemMeta, marginTop: "0.2rem" }}>
                {selectedKind}
                {extOf(selected) ? ` · .${extOf(selected)}` : ""}
              </div>
            </div>

            {/* TODO: The server does not yet expose assets via an MCP resource
                template (no `collateral://assets/{filename}` resource in
                server.py). Once it does, use synapse.readResource to pull
                bytes and render images with <img> or PDFs via PDFViewer,
                matching the preview flow in usePreview.ts. For now we show
                metadata only. */}
            <div
              style={{
                flex: 1,
                minHeight: 200,
                border: `1px dashed ${tokens.borderPrimary}`,
                borderRadius: tokens.radiusSm,
                background: tokens.bgTertiary,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: tokens.textSecondary,
                fontSize: tokens.textSm,
                padding: "1rem",
                textAlign: "center",
              }}
            >
              Inline previews for assets will appear once the server exposes
              asset bytes as a readable resource.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
