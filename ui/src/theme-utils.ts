import { useTheme } from "@nimblebrain/synapse/react";

const TOKEN_MAP: Record<string, string> = {
  background: "--color-background-primary",
  foreground: "--color-text-primary",
  card: "--color-background-secondary",
  primary: "--color-text-accent",
  border: "--color-border-primary",
  muted: "--color-text-secondary",
  secondary: "--color-background-secondary",
  destructive: "--nb-color-danger",
};

export type ThemeTokenFn = (token: string, fallback: string) => string;

export function useThemeTokens(): { t: ThemeTokenFn; theme: ReturnType<typeof useTheme> } {
  const theme = useTheme();
  const t: ThemeTokenFn = (token, fallback) =>
    theme.tokens[TOKEN_MAP[token] ?? token] || fallback;
  return { t, theme };
}
