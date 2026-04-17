export const RESPONSIVE_STYLES = `
.collateral-preview-pane .collateral-preview-frame { transition: box-shadow 180ms ease, border-color 180ms ease; }
.collateral-preview-pane a[aria-label="Download PDF"]:hover { background: rgba(15, 23, 42, 0.06); color: inherit; }
.collateral-preview-pane a[aria-label="Download PDF"]:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.collateral-preview-dots span { display: inline-block; opacity: 0; animation: collateral-dot 1.4s infinite; }
.collateral-preview-dots span:nth-child(2) { animation-delay: 0.2s; }
.collateral-preview-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes collateral-dot { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
.collateral-pdf-viewer-btn { background: none; border: 1px solid transparent; color: inherit; cursor: pointer; font-family: inherit; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.72rem; line-height: 1; display: inline-flex; align-items: center; justify-content: center; }
.collateral-pdf-viewer-btn:hover:not(:disabled) { background: rgba(15, 23, 42, 0.06); }
.collateral-pdf-viewer-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.collateral-pdf-viewer-zoomlabel { font-variant-numeric: tabular-nums; min-width: 3ch; text-align: center; font-size: 0.7rem; }
@media (max-width: 640px) {
  .collateral-preview-pane { padding: 0 !important; }
  .collateral-preview-pane .collateral-preview-frame { border-radius: 0; border-left: 0; border-right: 0; box-shadow: none; }
  .collateral-pdf-viewer-zoomlabel { display: none; }
}
@media (prefers-color-scheme: dark) {
  .collateral-preview-pane a[aria-label="Download PDF"]:hover { background: rgba(255, 255, 255, 0.08); }
  .collateral-pdf-viewer-btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.08); }
}
`;

let stylesInjected = false;
export function injectResponsiveStyles() {
  if (stylesInjected) return;
  stylesInjected = true;
  const el = document.createElement("style");
  el.textContent = RESPONSIVE_STYLES;
  document.head.appendChild(el);
}
