import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
// unpdf ships a serverless PDF.js build with the worker inlined, so no
// separate worker file is needed in the browser.
import { getDocumentProxy } from "unpdf";
import { tokens } from "../styles";

interface PDFViewerProps {
  blob: Blob;
  onDownload?: () => void | Promise<void>;
}

const MIN_SCALE = 0.25;
const MAX_SCALE = 4;
const STEP_IN = 1.25;
const STEP_OUT = 0.8;
const CACHE_CAP = 10;

// PDF.js types we actually touch. Using narrow shapes instead of pulling the
// full pdfjs-dist typing surface.
interface PdfViewport {
  width: number;
  height: number;
}
interface PdfPage {
  getViewport(opts: { scale: number }): PdfViewport;
  render(opts: { canvasContext: CanvasRenderingContext2D; viewport: PdfViewport }): {
    promise: Promise<void>;
    cancel: () => void;
  };
}
interface PdfDocument {
  numPages: number;
  getPage(n: number): Promise<PdfPage>;
}

type PageCache = Map<string, ImageBitmap>;

function cacheKey(page: number, scale: number, dpr: number) {
  return `${page}@${scale.toFixed(3)}x${dpr.toFixed(2)}`;
}

export function PDFViewer({ blob, onDownload }: PDFViewerProps) {
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const docRef = useRef<PdfDocument | null>(null);

  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const [nativeWidth, setNativeWidth] = useState<number | null>(null);
  const [nativeHeight, setNativeHeight] = useState<number | null>(null);
  const [scale, setScale] = useState(1);
  const [userZoom, setUserZoom] = useState(false);
  const [ready, setReady] = useState(false);
  const [renderError, setRenderError] = useState("");

  const cacheRef = useRef<PageCache>(new Map());
  const renderSeq = useRef(0);

  // Load the PDF, keep the doc proxy in a ref, and read the first page viewport.
  useEffect(() => {
    let cancelled = false;
    setReady(false);
    setPage(1);
    setPageCount(1);
    setNativeWidth(null);
    setNativeHeight(null);
    setUserZoom(false);
    setScale(1);
    setRenderError("");
    // Free any cached bitmaps from the previous PDF.
    for (const bmp of cacheRef.current.values()) bmp.close();
    cacheRef.current = new Map();
    docRef.current = null;

    (async () => {
      try {
        const buf = new Uint8Array(await blob.arrayBuffer());
        if (cancelled) return;
        const doc = (await getDocumentProxy(new Uint8Array(buf))) as unknown as PdfDocument;
        if (cancelled) return;
        docRef.current = doc;
        setPageCount(doc.numPages);
        const firstPage = await doc.getPage(1);
        if (cancelled) return;
        const viewport = firstPage.getViewport({ scale: 1 });
        setNativeWidth(viewport.width);
        setNativeHeight(viewport.height);
        setReady(true);
      } catch (e) {
        if (cancelled) return;
        setRenderError(e instanceof Error ? e.message : "Failed to load PDF");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [blob]);

  // Fit the whole page into the container (min of width/height axes). Fit both
  // axes + floor + generous gutter keep the rendered page strictly smaller
  // than the container so no scrollbar can appear in fit mode.
  const recomputeFitScale = useCallback(() => {
    if (!nativeWidth || !nativeHeight || !bodyRef.current) return;
    const cw = bodyRef.current.clientWidth;
    const ch = bodyRef.current.clientHeight;
    if (cw <= 0 || ch <= 0) return;
    const fitW = (cw - 24) / nativeWidth;
    const fitH = (ch - 24) / nativeHeight;
    const target = Math.min(fitW, fitH);
    const clamped = Math.min(MAX_SCALE, Math.max(MIN_SCALE, target));
    const quantized = Math.floor(clamped * 100) / 100;
    setScale((prev) => (prev === quantized ? prev : quantized));
  }, [nativeWidth, nativeHeight]);

  useLayoutEffect(() => {
    if (userZoom) return;
    recomputeFitScale();
  }, [nativeHeight, nativeWidth, userZoom, recomputeFitScale]);

  useEffect(() => {
    const el = bodyRef.current;
    if (!el) return;
    if (typeof ResizeObserver === "undefined") return;
    let rafId = 0;
    const ro = new ResizeObserver(() => {
      if (userZoom) return;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        rafId = 0;
        recomputeFitScale();
      });
    });
    ro.observe(el);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, [userZoom, recomputeFitScale]);

  // Render the current page + scale into the canvas. PDF.js draws directly into
  // the 2D context — no intermediate PNG, no data URL. Rendered frames are
  // cached as ImageBitmaps so re-fits and zoom-backs are instant blits.
  useEffect(() => {
    if (!ready || !docRef.current || !nativeWidth || !nativeHeight) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
    const backingW = Math.round(nativeWidth * scale * dpr);
    const backingH = Math.round(nativeHeight * scale * dpr);
    const cssW = backingW / dpr;
    const cssH = backingH / dpr;

    // Size the canvas up front so layout is stable before async work.
    if (canvas.width !== backingW) canvas.width = backingW;
    if (canvas.height !== backingH) canvas.height = backingH;
    canvas.style.width = `${cssW}px`;
    canvas.style.height = `${cssH}px`;

    const key = cacheKey(page, scale, dpr);
    const cached = cacheRef.current.get(key);
    if (cached) {
      ctx.clearRect(0, 0, backingW, backingH);
      ctx.drawImage(cached, 0, 0);
      return;
    }

    const seq = ++renderSeq.current;
    let task: { cancel: () => void } | null = null;

    (async () => {
      try {
        const doc = docRef.current;
        if (!doc) return;
        const pdfPage = await doc.getPage(page);
        if (seq !== renderSeq.current) return;
        const viewport = pdfPage.getViewport({ scale: scale * dpr });
        ctx.clearRect(0, 0, backingW, backingH);
        const renderTask = pdfPage.render({ canvasContext: ctx, viewport });
        task = renderTask;
        await renderTask.promise;
        if (seq !== renderSeq.current) return;
        // Cache the rendered frame as an ImageBitmap (GPU-transferable).
        const bitmap = await createImageBitmap(canvas);
        if (seq !== renderSeq.current) {
          bitmap.close();
          return;
        }
        const cache = cacheRef.current;
        cache.set(key, bitmap);
        while (cache.size > CACHE_CAP) {
          const oldestKey = cache.keys().next().value;
          if (oldestKey === undefined) break;
          const victim = cache.get(oldestKey);
          cache.delete(oldestKey);
          victim?.close();
        }
      } catch (e: unknown) {
        if (seq !== renderSeq.current) return;
        // PDF.js throws a "RenderingCancelledException" when a previous
        // render is superseded — that's expected, not a user-facing error.
        const msg = e instanceof Error ? e.message : String(e);
        if (/cancelled/i.test(msg)) return;
        setRenderError(msg);
      }
    })();

    return () => {
      task?.cancel();
    };
  }, [ready, page, scale, nativeWidth, nativeHeight]);

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

  // Free cached bitmaps on unmount.
  useEffect(() => {
    const cache = cacheRef.current;
    return () => {
      for (const bmp of cache.values()) bmp.close();
      cache.clear();
    };
  }, []);

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

  return (
    <div
      className="collateral-pdf-viewer"
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        className="collateral-pdf-toolbar"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.35rem",
          padding: "0.5rem 0.75rem",
          borderBottom: `1px solid ${tokens.borderPrimary}`,
          color: tokens.textSecondary,
          fontSize: tokens.textSm,
          lineHeight: tokens.textSmLh,
          flexShrink: 0,
          background: tokens.bgSecondary,
        }}
      >
        <button
          type="button"
          className="collateral-pdf-viewer-btn"
          onClick={handleZoomOut}
          disabled={scale <= MIN_SCALE + 1e-6}
          aria-label="Zoom out"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
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
        {onDownload && (
          <button
            type="button"
            onClick={() => void onDownload()}
            aria-label="Download PDF"
            className="collateral-pdf-viewer-btn collateral-pdf-viewer-download"
            style={{ marginLeft: "auto" }}
          >
            <svg
              width="16"
              height="16"
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
          </button>
        )}
      </div>

      <div
        ref={bodyRef}
        className="collateral-pdf-body"
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          background: tokens.bgTertiary,
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "0.75rem",
        }}
      >
        {renderError ? (
          <div
            style={{
              color: tokens.danger,
              fontSize: tokens.textSm,
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            {renderError}
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            aria-label={`Page ${page}`}
            style={{
              display: "block",
              // In fit mode, CSS-cap so the canvas can never overflow the
              // container even by a pixel. In user-zoom mode, let natural
              // size drive so scroll works.
              maxWidth: userZoom ? "none" : "100%",
              maxHeight: userZoom ? "none" : "100%",
              boxShadow: tokens.shadowMd,
              background: "#fff",
            }}
          />
        )}
        {!ready && !renderError && (
          <div
            className="collateral-preview-dots"
            style={{
              position: "absolute",
              color: tokens.textSecondary,
              fontSize: tokens.textSm,
              padding: "1.5rem",
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
          className="collateral-pdf-pager"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.4rem 0.75rem",
            borderTop: `1px solid ${tokens.borderPrimary}`,
            color: tokens.textSecondary,
            fontSize: tokens.textSm,
            flexShrink: 0,
            background: tokens.bgSecondary,
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
          <span style={{ minWidth: "7ch", textAlign: "center" }}>
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
