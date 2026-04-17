import { useEffect, useMemo, useState } from "react";
import { useSynapse } from "@nimblebrain/synapse/react";
import { s, tokens } from "../styles";
import { AssetUpload } from "../components/AssetUpload";
import { PDFViewer } from "../components/PDFViewer";
import { fetchResourceAsBlob } from "../resources";

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
  const synapse = useSynapse();
  const [selected, setSelected] = useState<string | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedKind = useMemo(
    () => (selected ? kindOf(selected) : null),
    [selected],
  );

  useEffect(() => {
    let cancelled = false;
    setBlob(null);
    setImageUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setError("");

    if (!selected) return;
    if (selectedKind === "other") return;

    setLoading(true);
    (async () => {
      try {
        const fetched = await fetchResourceAsBlob(
          synapse,
          `collateral://assets/${encodeURIComponent(selected)}`,
        );
        if (cancelled) return;
        if (selectedKind === "image") {
          const url = URL.createObjectURL(fetched);
          setImageUrl(url);
        } else {
          setBlob(fetched);
        }
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load asset");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selected, selectedKind, synapse]);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  return (
    <div className="collateral-main-layout" style={s.mainLayout}>
      <div className="collateral-left-panel" style={s.leftPanel}>
        <div style={{ ...s.listHeader, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <AssetUpload onUpload={onUpload} onAfterUpload={onRefresh} compact />
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
        ) : error ? (
          <div style={{ ...s.previewStatus, color: tokens.danger }}>{error}</div>
        ) : loading ? (
          <div style={s.previewStatus}>
            <span className="collateral-preview-dots" aria-label="Loading">
              Loading<span>.</span>
              <span>.</span>
              <span>.</span>
            </span>
          </div>
        ) : selectedKind === "pdf" && blob ? (
          <PDFViewer blob={blob} />
        ) : selectedKind === "image" && imageUrl ? (
          <div
            style={{
              flex: 1,
              minHeight: 0,
              overflow: "auto",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "1.25rem",
              background: tokens.bgTertiary,
            }}
          >
            <img
              src={imageUrl}
              alt={selected}
              style={{
                maxWidth: "100%",
                maxHeight: "100%",
                display: "block",
                boxShadow: tokens.shadowMd,
                background: "#fff",
              }}
            />
          </div>
        ) : (
          <div
            style={{
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              padding: "1.25rem",
              gap: "0.5rem",
              overflow: "auto",
            }}
          >
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
            <div style={s.listItemMeta}>
              {selectedKind}
              {extOf(selected) ? ` · .${extOf(selected)}` : ""}
            </div>
            <div
              style={{
                marginTop: "1rem",
                color: tokens.textSecondary,
                fontSize: tokens.textSm,
              }}
            >
              Inline preview isn't available for this file type.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
