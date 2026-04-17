import type { ReactNode } from "react";
import { s } from "../styles";

interface DialogProps {
  onClose: () => void;
  children: ReactNode;
  width?: number;
}

export function Dialog({ onClose, children, width }: DialogProps) {
  return (
    <div
      style={s.overlay}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="collateral-dialog"
        style={{
          ...s.dialog,
          ...(width ? { width } : {}),
        }}
      >
        {children}
      </div>
    </div>
  );
}
