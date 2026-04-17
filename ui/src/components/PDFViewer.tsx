import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
// unpdf ships a serverless PDF.js build with the worker inlined, so no
// separate worker file is needed in the browser.
import { getDocumentProxy, renderPageAsImage } from "unpdf";
import { useThemeTokens } from "../theme-utils";

interface PDFViewerProps {
  blob: Blob;
  downloadUrl?: string;
  downloadFilename?: string;
}

const MIN_SCALE = 0.25;
const MAX_SCALE = 4;
const STEP_IN = 1.25;
const STEP_OUT = 0.8;
const CACHE_CAP = 10;

type PageCache = Map<string, string>;

function cacheKey(page: number, scale: number) {
  return `${page}@${scale.toFixed(3)}`;
}

export function PDFViewer({ blob, downloadUrl, downloadFilename }: PDFViewerProps) {
  const { t } = useThemeTokens();
  const bodyRef = useRef<HTMLDivElement | null>(null);

  // Immutable snapshot of the PDF bytes. unpdf transfers the underlying buffer,
  // so we keep a Uint8Array per render and clone it for each invocation.
  const [pdfBytes, setPdfBytes] = useState<Uint8Array | null>(null);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const [nativeWidth, setNativeWidth] = useState<number | null>(null);
  const [nativeHeight, setNativeHeight] = useState<number | null>(null);
  const [scale, setScale] = useState(1);
  const [userZoom, setUserZoom] = useState(false);
  const [dataUrl, setDataUrl] = useState<string | null>(null);
  const [renderError, setRenderError] = useState("");

  const cacheRef = useRef<PageCache>(new Map());
  const renderSeq = useRef(0);

  // Load document when blob changes.
  useEffect(() => {
    let cancelled = false;
    setPdfBytes(null);
    setDataUrl(null);
    setPage(1);
    setPageCount(1);
    setNativeWidth(null);
    setNativeHeight(null);
    setUserZoom(false);
    setScale(1);
    setRenderError("");
    cacheRef.current = new Map();

    (async () => {
      try {
        const buf = new Uint8Array(await blob.arrayBuffer());
        if (cancelled) return;
        // Clone for getDocumentProxy so we keep an untouched copy for renders.
        const doc = await getDocumentProxy(new Uint8Array(buf));
        if (cancelled) return;
        setPageCount(doc.numPages);
        const firstPage = await doc.getPage(1);
        if (cancelled) return;
        const viewport = firstPage.getViewport({ scale: 1 });
        setNativeWidth(viewport.width);
        setNativeHeight(viewport.height);
        setPdfBytes(buf);
      } catch (e) {
        if (cancelled) return;
        setRenderError(e instanceof Error ? e.message : "Failed to load PDF");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [blob]);

  // Compute fit-to-height scale based on body height vs. native page height.
  const recomputeFitScale = useCallback(() => {
    if (!nativeHeight || !bodyRef.current) return;
    const ch = bodyRef.current.clientHeight;
    if (ch <= 0) return;
    // Leave a small gutter so the image doesn't touch the scrollbar edge.
    const target = Math.max(0.1, (ch - 16) / nativeHeight);
    setScale(Math.min(MAX_SCALE, Math.max(MIN_SCALE, target)));
  }, [nativeHeight]);

  // Recompute fit scale on first layout after native dimensions resolve.
  useLayoutEffect(() => {
    if (userZoom) return;
    recomputeFitScale();
  }, [nativeHeight, userZoom, recomputeFitScale]);

  // Observe container resizes and rescale to fit width (until user zooms).
  useEffect(() => {
    const el = bodyRef.current;
    if (!el) return;
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      if (!userZoom) recomputeFitScale();
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [userZoom, recomputeFitScale]);

  // Render current page at current scale. Uses a per-blob cache keyed by
  // (page, scale) to make zoom repeats instant.
  useEffect(() => {
    if (!pdfBytes || !nativeWidth) return;
    const key = cacheKey(page, scale);
    const cached = cacheRef.current.get(key);
    if (cached) {
      setDataUrl(cached);
      return;
    }
    const seq = ++renderSeq.current;
    (async () => {
      try {
        const url = await renderPageAsImage(new Uint8Array(pdfBytes), page, {
          scale,
          toDataURL: true,
        });
        if (seq !== renderSeq.current) return;
        const cache = cacheRef.current;
        cache.set(key, url);
        // Cap the cache. Delete oldest entries first (insertion-ordered).
        while (cache.size > CACHE_CAP) {
          const oldest = cache.keys().next().value;
          if (oldest === undefined) break;
          cache.delete(oldest);
        }
        setDataUrl(url);
      } catch (e) {
        if (seq !== renderSeq.current) return;
        setRenderError(e instanceof Error ? e.message : "Render failed");
      }
    })();
  }, [pdfBytes, page, scale, nativeWidth]);

  // Keyboard nav for multi-page docs.
  useEffect(() => {
    if (pageCount < 2) return;
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      if (e.key === "ArrowRight") {
        setPage((p) => Math.min(pageCount, p + 1));
      } else if (e.key === "ArrowLeft") {
        setPage((p) => Math.max(1, p - 1));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [pageCount]);

  const handleZoomIn = () => {
    setUserZoom(true);
    setScale((s) => Math.min(MAX_SCALE, s * STEP_IN));
  };
  const handleZoomOut = () => {
    setUserZoom(true);
    setScale((s) => Math.max(MIN_SCALE, s * STEP_OUT));
  };
  const handleFit = () => {
    setUserZoom(false);
    recomputeFitScale();
  };

  const zoomPct = useMemo(() => `${Math.round(scale * 100)}%`, [scale]);

  const border = t("border", "#e5e7eb");
  const muted = t("muted", "#6b7280");
  const surface = t("secondary", "#f3f4f6");
  const background = t("background", "#ffffff");

  return (
    <div
      className="collateral-pdf-viewer"
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background,
        border: `1px solid ${border}`,
        borderRadius: 10,
        overflow: "hidden",
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.25rem",
          padding: "0.3rem 0.5rem",
          borderBottom: `1px solid ${border}`,
          color: muted,
          fontSize: "0.72rem",
          flexShrink: 0,
        }}
      >
        <button
          type="button"
          className="collateral-pdf-viewer-btn"
          onClick={handleZoomOut}
          disabled={scale <= MIN_SCALE + 1e-6}
          aria-label="Zoom out"
        >
          −
        </button>
        <span className="collateral-pdf-viewer-zoomlabel" aria-live="polite">
          {zoomPct}
        </span>
        <button
          type="button"
          className="collateral-pdf-viewer-btn"
          onClick={handleZoomIn}
          disabled={scale >= MAX_SCALE - 1e-6}
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          type="button"
          className="collateral-pdf-viewer-btn"
          onClick={handleFit}
          aria-label="Fit to page"
          style={{ marginLeft: "0.25rem" }}
        >
          Fit
        </button>
        {downloadUrl && (
          <a
            href={downloadUrl}
            download={downloadFilename ?? "document.pdf"}
            aria-label="Download PDF"
            className="collateral-pdf-viewer-download"
            style={{
              marginLeft: "auto",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 24,
              height: 24,
              borderRadius: 5,
              color: muted,
              textDecoration: "none",
            }}
          >
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
              <path d="M12 3v12" />
              <path d="m7 10 5 5 5-5" />
              <path d="M5 21h14" />
            </svg>
          </a>
        )}
      </div>

      <div
        ref={bodyRef}
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          background: surface,
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "0.5rem",
        }}
      >
        {renderError ? (
          <div
            style={{
              color: t("destructive", "#ef4444"),
              fontSize: "0.82rem",
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            {renderError}
          </div>
        ) : dataUrl ? (
          <img
            src={dataUrl}
            alt={`Page ${page}`}
            style={{
              display: "block",
              maxWidth: "none",
              height: "auto",
              boxShadow: "0 1px 3px rgba(15, 23, 42, 0.08), 0 4px 12px rgba(15, 23, 42, 0.08)",
              background: "#fff",
            }}
          />
        ) : (
          <div
            className="collateral-preview-dots"
            style={{
              color: muted,
              fontSize: "0.82rem",
              padding: "1.5rem",
              textAlign: "center",
            }}
            aria-label="Rendering"
          >
            Rendering<span>.</span>
            <span>.</span>
            <span>.</span>
          </div>
        )}
      </div>

      {pageCount > 1 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.3rem 0.5rem",
            borderTop: `1px solid ${border}`,
            color: muted,
            fontSize: "0.72rem",
            flexShrink: 0,
          }}
        >
          <button
            type="button"
            className="collateral-pdf-viewer-btn"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            aria-label="Previous page"
          >
            ‹
          </button>
          <span style={{ minWidth: "6ch", textAlign: "center" }}>
            Page {page} of {pageCount}
          </span>
          <button
            type="button"
            className="collateral-pdf-viewer-btn"
            onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
            disabled={page >= pageCount}
            aria-label="Next page"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}
