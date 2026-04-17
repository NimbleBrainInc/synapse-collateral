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

.collateral-dialog-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.25rem;
  flex-wrap: wrap;
}

.collateral-logo-mark { display: none; }
.collateral-logo-full { display: inline; }
`;

let stylesInjected = false;
export function injectResponsiveStyles() {
  if (stylesInjected) return;
  stylesInjected = true;
  const el = document.createElement("style");
  el.textContent = RESPONSIVE_STYLES;
  document.head.appendChild(el);
}
