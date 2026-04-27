import type { CSSProperties } from "react";

// Design tokens resolve from CSS variables the host injects. Each var() falls
// back to the light-mode default so static/standalone renders still look sane.
const FONT_SANS =
  "var(--font-sans, 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif)";
const FONT_MONO =
  "var(--font-mono, 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace)";
const FONT_HEADING =
  "var(--nb-font-heading, 'Erode', Georgia, 'Times New Roman', serif)";

const TEXT_XS = "var(--font-text-xs-size, 0.75rem)";
const TEXT_XS_LH = "var(--font-text-xs-line-height, 1rem)";
const TEXT_SM = "var(--font-text-sm-size, 0.875rem)";
const TEXT_SM_LH = "var(--font-text-sm-line-height, 1.25rem)";
const TEXT_BASE = "var(--font-text-base-size, 1rem)";
const TEXT_BASE_LH = "var(--font-text-base-line-height, 1.5rem)";
const HEADING_SM = "var(--font-heading-sm-size, 1.25rem)";
const HEADING_SM_LH = "var(--font-heading-sm-line-height, 1.75rem)";

const WEIGHT_NORMAL = "var(--font-weight-normal, 400)";
const WEIGHT_MEDIUM = "var(--font-weight-medium, 500)";
const WEIGHT_SEMIBOLD = "var(--font-weight-semibold, 600)";

const BG_PRIMARY = "var(--color-background-primary, #faf9f7)";
const BG_SECONDARY = "var(--color-background-secondary, #ffffff)";
const BG_TERTIARY = "var(--color-background-tertiary, #f3f2ef)";
const TEXT_PRIMARY = "var(--color-text-primary, #171717)";
const TEXT_SECONDARY = "var(--color-text-secondary, #737373)";
const TEXT_ACCENT = "var(--color-text-accent, #0055FF)";
const BORDER_PRIMARY = "var(--color-border-primary, #e5e5e5)";
const RING = "var(--color-ring-primary, #0055FF)";
const ACCENT_FG = "var(--nb-color-accent-foreground, #ffffff)";
const DANGER = "var(--nb-color-danger, #dc2626)";

const RADIUS_XS = "var(--border-radius-xs, 0.25rem)";
const RADIUS_SM = "var(--border-radius-sm, 0.5rem)";
const RADIUS_MD = "var(--border-radius-md, 0.75rem)";
const RADIUS_LG = "var(--border-radius-lg, 1rem)";

const SHADOW_SM = "var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05))";
const SHADOW_MD = "var(--shadow-md, 0 4px 6px -1px rgba(0,0,0,0.1))";
const SHADOW_LG = "var(--shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1))";

export const tokens = {
  fontSans: FONT_SANS,
  fontMono: FONT_MONO,
  fontHeading: FONT_HEADING,
  textXs: TEXT_XS,
  textXsLh: TEXT_XS_LH,
  textSm: TEXT_SM,
  textSmLh: TEXT_SM_LH,
  textBase: TEXT_BASE,
  textBaseLh: TEXT_BASE_LH,
  headingSm: HEADING_SM,
  headingSmLh: HEADING_SM_LH,
  weightNormal: WEIGHT_NORMAL,
  weightMedium: WEIGHT_MEDIUM,
  weightSemibold: WEIGHT_SEMIBOLD,
  bgPrimary: BG_PRIMARY,
  bgSecondary: BG_SECONDARY,
  bgTertiary: BG_TERTIARY,
  textPrimary: TEXT_PRIMARY,
  textSecondary: TEXT_SECONDARY,
  textAccent: TEXT_ACCENT,
  borderPrimary: BORDER_PRIMARY,
  ring: RING,
  accentFg: ACCENT_FG,
  danger: DANGER,
  radiusXs: RADIUS_XS,
  radiusSm: RADIUS_SM,
  radiusMd: RADIUS_MD,
  radiusLg: RADIUS_LG,
  shadowSm: SHADOW_SM,
  shadowMd: SHADOW_MD,
  shadowLg: SHADOW_LG,
} as const;

export const s: Record<string, CSSProperties> = {
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
    fontFamily: FONT_SANS,
    fontSize: TEXT_SM,
    lineHeight: TEXT_SM_LH,
    color: TEXT_PRIMARY,
    background: BG_PRIMARY,
  },
  nav: {
    display: "flex",
    alignItems: "center",
    borderBottom: `1px solid ${BORDER_PRIMARY}`,
    padding: "0 1rem",
    height: 48,
    flexShrink: 0,
    gap: "0.5rem",
    background: BG_SECONDARY,
  },
  logo: {
    fontFamily: FONT_HEADING,
    fontWeight: WEIGHT_SEMIBOLD,
    fontSize: TEXT_BASE,
    letterSpacing: "-0.01em",
    marginRight: "0.75rem",
    color: TEXT_PRIMARY,
    whiteSpace: "nowrap",
  },
  tabGroup: {
    display: "flex",
    gap: 0,
    height: "100%",
    alignItems: "stretch",
  },
  tabBtn: {
    padding: "0 0.85rem",
    fontSize: TEXT_SM,
    background: "none",
    border: "none",
    borderBottom: "2px solid transparent",
    cursor: "pointer",
    fontFamily: "inherit",
    color: TEXT_SECONDARY,
    fontWeight: WEIGHT_MEDIUM,
    display: "inline-flex",
    alignItems: "center",
  },
  tabBtnActive: {
    color: TEXT_ACCENT,
    borderBottomColor: TEXT_ACCENT,
  },
  mainLayout: {
    flex: 1,
    display: "flex",
    overflow: "hidden",
    minHeight: 0,
  },
  leftPanel: {
    width: 280,
    minWidth: 220,
    maxWidth: 360,
    borderRight: `1px solid ${BORDER_PRIMARY}`,
    display: "flex",
    flexDirection: "column",
    flexShrink: 0,
    background: BG_SECONDARY,
  },
  listHeader: {
    padding: "0.75rem",
    flexShrink: 0,
    borderBottom: `1px solid ${BORDER_PRIMARY}`,
  },
  listScroll: {
    flex: 1,
    overflowY: "auto",
  },
  listItem: {
    padding: "0.75rem 0.85rem",
    borderBottom: `1px solid ${BORDER_PRIMARY}`,
    cursor: "pointer",
    transition: "background 120ms ease",
  },
  listItemActive: {
    background: BG_TERTIARY,
  },
  listItemTitle: {
    fontWeight: WEIGHT_SEMIBOLD,
    fontSize: TEXT_SM,
    color: TEXT_PRIMARY,
  },
  listItemMeta: {
    fontSize: TEXT_XS,
    lineHeight: TEXT_XS_LH,
    color: TEXT_SECONDARY,
    marginTop: "0.15rem",
  },
  rightPanel: {
    flex: 1,
    minWidth: 0,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    background: BG_PRIMARY,
  },
  previewStatus: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: TEXT_SM,
    padding: "1.5rem",
    textAlign: "center",
    color: TEXT_SECONDARY,
  },
  sectionTitle: {
    fontSize: TEXT_XS,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    fontWeight: WEIGHT_SEMIBOLD,
    color: TEXT_SECONDARY,
    margin: "0 0 0.5rem",
  },
  dialogTitle: {
    fontFamily: FONT_HEADING,
    fontSize: HEADING_SM,
    lineHeight: HEADING_SM_LH,
    fontWeight: WEIGHT_SEMIBOLD,
    color: TEXT_PRIMARY,
    margin: "0 0 1rem",
    letterSpacing: "-0.01em",
  },
  textarea: {
    width: "100%",
    padding: "0.6rem 0.7rem",
    borderRadius: RADIUS_XS,
    border: `1px solid ${BORDER_PRIMARY}`,
    background: BG_PRIMARY,
    color: TEXT_PRIMARY,
    fontSize: TEXT_SM,
    lineHeight: TEXT_SM_LH,
    fontFamily: "inherit",
    outline: "none",
    minHeight: 140,
    resize: "vertical",
  },
  assetGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
    gap: "0.5rem",
  },
  assetCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "0.6rem",
    borderRadius: RADIUS_SM,
    border: `1px solid ${BORDER_PRIMARY}`,
    background: BG_SECONDARY,
    gap: "0.35rem",
  },
  assetThumb: {
    width: 64,
    height: 64,
    borderRadius: RADIUS_XS,
    background: BG_TERTIARY,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: TEXT_SECONDARY,
    fontSize: TEXT_XS,
    fontWeight: WEIGHT_SEMIBOLD,
    letterSpacing: "0.04em",
  },
  dashed: {
    border: `2px dashed ${BORDER_PRIMARY}`,
    justifyContent: "center",
    minHeight: 92,
    fontSize: TEXT_SM,
    color: TEXT_SECONDARY,
    background: "transparent",
  },
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.45)",
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "1rem",
  },
  dialog: {
    border: `1px solid ${BORDER_PRIMARY}`,
    borderRadius: RADIUS_MD,
    padding: "1.25rem",
    width: 380,
    maxWidth: "100%",
    boxShadow: SHADOW_LG,
    background: BG_SECONDARY,
    color: TEXT_PRIMARY,
  },
  templateOpt: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    padding: "0.55rem 0.7rem",
    border: `1px solid ${BORDER_PRIMARY}`,
    borderRadius: RADIUS_XS,
    background: BG_PRIMARY,
    color: TEXT_PRIMARY,
    cursor: "pointer",
    fontSize: TEXT_SM,
  },
  templateOptActive: {
    borderColor: RING,
    background: BG_TERTIARY,
  },
  label: {
    display: "block",
    fontSize: TEXT_XS,
    lineHeight: TEXT_XS_LH,
    fontWeight: WEIGHT_MEDIUM,
    color: TEXT_SECONDARY,
    marginBottom: "0.3rem",
  },
  input: {
    width: "100%",
    padding: "0.5rem 0.7rem",
    borderRadius: RADIUS_XS,
    border: `1px solid ${BORDER_PRIMARY}`,
    background: BG_PRIMARY,
    color: TEXT_PRIMARY,
    fontSize: TEXT_SM,
    lineHeight: TEXT_SM_LH,
    fontFamily: "inherit",
    outline: "none",
  },
  btn: {
    padding: "0 0.85rem",
    height: 32,
    borderRadius: RADIUS_XS,
    border: "1px solid transparent",
    fontSize: TEXT_SM,
    cursor: "pointer",
    fontWeight: WEIGHT_MEDIUM,
    whiteSpace: "nowrap",
    fontFamily: "inherit",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.35rem",
    lineHeight: 1,
    transition: "background 120ms ease, border-color 120ms ease, color 120ms ease",
  },
  btnPrimary: {
    background: TEXT_ACCENT,
    color: ACCENT_FG,
    borderColor: TEXT_ACCENT,
  },
  btnGhost: {
    background: "transparent",
    color: TEXT_PRIMARY,
    borderColor: BORDER_PRIMARY,
  },
  btnDanger: {
    background: DANGER,
    color: ACCENT_FG,
    borderColor: DANGER,
  },
  btnIcon: {
    background: "transparent",
    border: "1px solid transparent",
    color: TEXT_SECONDARY,
    cursor: "pointer",
    fontFamily: "inherit",
    padding: "0.25rem",
    borderRadius: RADIUS_XS,
    fontSize: TEXT_XS,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    lineHeight: 1,
  },
  smallBtn: {
    padding: "0.25rem 0.55rem",
    height: 26,
    borderRadius: RADIUS_XS,
    border: `1px solid ${BORDER_PRIMARY}`,
    fontSize: TEXT_XS,
    cursor: "pointer",
    background: "transparent",
    color: TEXT_PRIMARY,
    fontFamily: "inherit",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    lineHeight: 1,
  },
};
