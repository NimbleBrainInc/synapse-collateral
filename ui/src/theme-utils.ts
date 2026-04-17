import { useEffect } from "react";
import { useTheme } from "@nimblebrain/synapse/react";

/**
 * Copies the host's theme tokens onto :root as CSS custom properties on every
 * change. Stylesheets and inline styles then consume values via var(--token).
 * Synapse re-emits the full token map when the host flips modes, so dark-mode
 * support is automatic — no data-attribute toggling required.
 */
export function useInjectThemeTokens(): {
  mode: "light" | "dark";
  accent: string;
} {
  const theme = useTheme();

  useEffect(() => {
    const root = document.documentElement;
    for (const [key, value] of Object.entries(theme.tokens)) {
      root.style.setProperty(key, value);
    }
    root.style.colorScheme = theme.mode;
  }, [theme.tokens, theme.mode]);

  return {
    mode: theme.mode,
    accent:
      theme.tokens["--color-text-accent"] ||
      theme.primaryColor ||
      "#0055FF",
  };
}

// Legacy token lookup — kept during the migration to pure CSS variables. New
// code should reference var(--token) in styles directly.
const LEGACY_TOKEN_MAP: Record<string, string> = {
  background: "--color-background-primary",
  foreground: "--color-text-primary",
  card: "--color-background-secondary",
  primary: "--color-text-accent",
  border: "--color-border-primary",
  muted: "--color-text-secondary",
  secondary: "--color-background-tertiary",
  destructive: "--nb-color-danger",
};

export type ThemeTokenFn = (token: string, fallback: string) => string;

export function useThemeTokens(): {
  t: ThemeTokenFn;
  theme: ReturnType<typeof useTheme>;
} {
  const theme = useTheme();
  const t: ThemeTokenFn = (token, fallback) =>
    theme.tokens[LEGACY_TOKEN_MAP[token] ?? token] || fallback;
  return { t, theme };
}
