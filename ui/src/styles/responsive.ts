export const RESPONSIVE_STYLES = `
html, body, #root {
  height: 100%;
  margin: 0;
}
body {
  font-family: var(--font-sans, 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif);
  background: var(--color-background-primary, #faf9f7);
  color: var(--color-text-primary, #171717);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
* { box-sizing: border-box; }

.collateral-root button:focus-visible,
.collateral-root a:focus-visible,
.collateral-root input:focus-visible,
.collateral-root textarea:focus-visible,
.collateral-root [role="tab"]:focus-visible {
  outline: 2px solid var(--color-ring-primary, #0055FF);
  outline-offset: 2px;
}

.collateral-root input:focus,
.collateral-root textarea:focus {
  border-color: var(--color-ring-primary, #0055FF);
}

.collateral-root button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.collateral-tab:hover:not(.collateral-tab-active) {
  color: var(--color-text-primary, #171717);
}

.collateral-topnav-actions button:hover:not(:disabled) {
  background: var(--color-background-tertiary, #f3f2ef);
}

.collateral-preview-dots span { display: inline-block; opacity: 0; animation: collateral-dot 1.4s infinite; }
.collateral-preview-dots span:nth-child(2) { animation-delay: 0.2s; }
.collateral-preview-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes collateral-dot { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

.collateral-pdf-viewer-btn {
  background: none;
  border: 1px solid transparent;
  color: inherit;
  cursor: pointer;
  font-family: inherit;
  padding: 0.3rem 0.55rem;
  border-radius: var(--border-radius-xs, 0.25rem);
  font-size: var(--font-text-sm-size, 0.875rem);
  line-height: 1;
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
}
.collateral-pdf-viewer-btn:hover:not(:disabled) {
  background: var(--color-background-tertiary, #f3f2ef);
  color: var(--color-text-primary, #171717);
}
.collateral-pdf-viewer-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.collateral-pdf-viewer-zoomlabel {
  font-variant-numeric: tabular-nums;
  min-width: 3.5ch;
  text-align: center;
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-primary, #171717);
  font-weight: var(--font-weight-medium, 500);
}

.collateral-overflow-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  min-width: 200px;
  background: var(--color-background-secondary, #ffffff);
  border: 1px solid var(--color-border-primary, #e5e5e5);
  border-radius: var(--border-radius-sm, 0.5rem);
  box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1));
  padding: 0.25rem;
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.collateral-overflow-menu button {
  background: none;
  border: 0;
  font-family: inherit;
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-primary, #171717);
  padding: 0.5rem 0.7rem;
  text-align: left;
  border-radius: var(--border-radius-xs, 0.25rem);
  cursor: pointer;
  display: block;
  width: 100%;
}
.collateral-overflow-menu button:hover:not(:disabled) {
  background: var(--color-background-tertiary, #f3f2ef);
}

.collateral-dialog-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.25rem;
  flex-wrap: wrap;
}

.collateral-logo-mark { display: none; }
.collateral-logo-full { display: inline; }
.collateral-overflow-btn { display: none; }

@media (max-width: 1024px) {
  .collateral-left-panel { width: 220px !important; min-width: 200px !important; }
}

@media (max-width: 768px) {
  .collateral-main-layout { flex-direction: column !important; }
  .collateral-left-panel {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    height: 40vh;
    flex-shrink: 0;
    border-right: 0 !important;
    border-bottom: 1px solid var(--color-border-primary, #e5e5e5);
  }
  .collateral-root button {
    min-height: 36px;
  }
  .collateral-pdf-toolbar .collateral-pdf-viewer-btn,
  .collateral-pdf-pager .collateral-pdf-viewer-btn {
    min-height: 40px;
    min-width: 40px;
    padding: 0.4rem 0.6rem;
  }
  .collateral-doc-actions { display: none !important; }
  .collateral-overflow-btn { display: inline-flex !important; }
}

@media (max-width: 640px) {
  .collateral-preview-pane { padding: 0 !important; }
  .collateral-pdf-viewer-zoomlabel { display: none; }
  .collateral-topnav { padding: 0 0.5rem !important; gap: 0.25rem !important; }
  .collateral-logo-full { display: none; }
  .collateral-logo-mark { display: inline; }
  .collateral-overlay {
    padding: 0 !important;
    align-items: stretch !important;
  }
  .collateral-dialog {
    width: 100% !important;
    max-width: 100% !important;
    border-radius: 0 !important;
    border-left: 0 !important;
    border-right: 0 !important;
    box-shadow: none !important;
    margin: auto 0;
  }
  .collateral-dialog-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }
  .collateral-dialog-actions button { width: 100%; }
  .collateral-settings-panel {
    width: 100vw !important;
    max-width: 100vw !important;
    border-left: 0 !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .collateral-preview-dots span { animation: none !important; opacity: 0.6 !important; }
  .collateral-root *, .collateral-root *::before, .collateral-root *::after {
    transition-duration: 0.001ms !important;
    animation-duration: 0.001ms !important;
  }
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
