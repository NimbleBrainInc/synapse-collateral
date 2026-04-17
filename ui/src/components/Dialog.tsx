import type { ReactNode } from "react";
import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";

interface DialogProps {
  onClose: () => void;
  children: ReactNode;
  width?: number;
}

export function Dialog({ onClose, children, width }: DialogProps) {
  const { t } = useThemeTokens();
  return (
    <div
      style={s.overlay}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          ...s.dialog,
          width: width ?? s.dialog.width,
          background: t("background", "#fff"),
          borderColor: t("border", "#e5e7eb"),
        }}
      >
        {children}
      </div>
    </div>
  );
}
