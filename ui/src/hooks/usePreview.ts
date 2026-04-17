import { useCallback, useEffect, useRef, useState } from "react";
import { useCallTool, useSynapse } from "@nimblebrain/synapse/react";
import { extractResourceUris, fetchResourceAsBlob } from "../resources";

export function usePreview() {
  const synapse = useSynapse();
  const previewTool = useCallTool("preview");
  const previewTemplateTool = useCallTool("preview_template");

  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Track the latest request so slower responses don't overwrite newer state.
  const requestId = useRef(0);

  useEffect(() => {
    return () => {
      // No blob URLs held here; PDFViewer manages its own data URL cache.
    };
  }, []);

  const clear = useCallback(() => {
    requestId.current++;
    setBlob(null);
    setError("");
    setLoading(false);
  }, []);

  const runPreviewTool = useCallback(
    async (runner: () => Promise<{ content?: unknown[] }>, errMsg: string) => {
      const id = ++requestId.current;
      setLoading(true);
      setError("");
      try {
        const result = await runner();
        if (id !== requestId.current) return;
        const [uri] = extractResourceUris(result.content ?? []);
        if (!uri) throw new Error("Preview returned no resource_link");
        const fetched = await fetchResourceAsBlob(synapse, uri);
        if (id !== requestId.current) return;
        setBlob(fetched);
      } catch (e) {
        if (id !== requestId.current) return;
        setError(e instanceof Error ? e.message : errMsg);
      } finally {
        if (id === requestId.current) setLoading(false);
      }
    },
    [synapse],
  );

  const previewDocument = useCallback(async () => {
    await runPreviewTool(() => previewTool.call({}), "Preview failed");
  }, [previewTool, runPreviewTool]);

  const previewTemplate = useCallback(
    async (templateId: string) => {
      await runPreviewTool(
        () => previewTemplateTool.call({ template_id: templateId }),
        "Failed to preview template",
      );
    },
    [previewTemplateTool, runPreviewTool],
  );

  return { blob, error, loading, previewDocument, previewTemplate, clear, setError };
}
