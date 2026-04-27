import { useEffect, useState } from "react";
import { s, tokens } from "../styles";
import { useComponents } from "../hooks/useComponents";

export function ComponentsView() {
  const { components, refresh, save, loading } = useComponents();
  const [draft, setDraft] = useState("");
  const [lastSaved, setLastSaved] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    setDraft(components);
    setLastSaved(components);
  }, [components]);

  const dirty = draft !== lastSaved;

  const handleSave = async () => {
    setSaving(true);
    setStatus(null);
    try {
      await save(draft);
      setLastSaved(draft);
      setStatus({ kind: "ok", text: "Components saved." });
      setTimeout(() => setStatus(null), 1500);
    } catch (e) {
      setStatus({ kind: "err", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        padding: "1.25rem",
        gap: "0.75rem",
        background: tokens.bgPrimary,
      }}
    >
      <div>
        <h2
          style={{
            fontFamily: tokens.fontHeading,
            fontSize: tokens.headingSm,
            lineHeight: tokens.headingSmLh,
            fontWeight: tokens.weightSemibold,
            color: tokens.textPrimary,
            letterSpacing: "-0.01em",
            margin: 0,
          }}
        >
          Reusable Components
        </h2>
        <p
          style={{
            fontSize: tokens.textSm,
            lineHeight: tokens.textSmLh,
            color: tokens.textSecondary,
            margin: "0.25rem 0 0",
          }}
        >
          Typst source available to every document via{" "}
          <code style={{ fontFamily: tokens.fontMono }}>#import "components.typ"</code>. Define
          shared layouts, callouts, or branding helpers here.
        </p>
      </div>

      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder={loading ? "Loading…" : "// Reusable Typst components\n\n#let callout(body) = block(\n  fill: rgb(\"#f3f4f6\"),\n  inset: 12pt,\n  body,\n)\n"}
        spellCheck={false}
        style={{
          flex: 1,
          minHeight: 0,
          width: "100%",
          padding: "0.85rem 1rem",
          border: `1px solid ${tokens.borderPrimary}`,
          borderRadius: "0.5rem",
          background: tokens.bgSecondary,
          color: tokens.textPrimary,
          fontFamily: tokens.fontMono,
          fontSize: tokens.textSm,
          lineHeight: 1.55,
          resize: "none",
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <button
          style={{ ...s.btn, ...s.btnPrimary }}
          onClick={handleSave}
          disabled={saving || !dirty}
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          style={{ ...s.btn, ...s.btnGhost }}
          onClick={() => setDraft(lastSaved)}
          disabled={saving || !dirty}
        >
          Reset
        </button>
        {status && (
          <span
            role={status.kind === "err" ? "alert" : "status"}
            style={{
              fontSize: tokens.textSm,
              color: status.kind === "ok" ? "#16a34a" : tokens.danger,
            }}
          >
            {status.text}
          </span>
        )}
      </div>
    </div>
  );
}
