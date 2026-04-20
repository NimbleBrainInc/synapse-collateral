import { useCallback, useEffect, useRef, useState } from "react";
import { useCallTool, useSynapse } from "@nimblebrain/synapse/react";
import { extractResourceUris, extractTextMessage, fetchResourceAsBlob } from "../resources";

type ToolResponse = { content?: unknown[]; isError?: boolean };

export function usePreview() {
  const synapse = useSynapse();
  const { call: previewCall } = useCallTool("preview");
  const { call: previewTemplateCall } = useCallTool("preview_template");

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
    async (runner: () => Promise<ToolResponse>, errMsg: string) => {
      const id = ++requestId.current;
      setLoading(true);
      setError("");
      try {
        const result = await runner();
        if (id !== requestId.current) return;
        // Tool surfaced an error (e.g. Typst compile failure, missing font,
        // corrupt asset). Clear stale preview so the user doesn't see an old
        // PDF while reading an error about the current source.
        if (result.isError) {
          const text = extractTextMessage(result.content ?? []);
          throw new Error(text || errMsg);
        }
        const [uri] = extractResourceUris(result.content ?? []);
        if (!uri) throw new Error("Preview returned no resource_link");
        const fetched = await fetchResourceAsBlob(synapse, uri);
        if (id !== requestId.current) return;
        setBlob(fetched);
      } catch (e) {
        if (id !== requestId.current) return;
        setBlob(null);
        setError(e instanceof Error ? e.message : errMsg);
      } finally {
        if (id === requestId.current) setLoading(false);
      }
    },
    [synapse],
  );

  const previewDocument = useCallback(async () => {
    await runPreviewTool(() => previewCall({}), "Preview failed");
  }, [previewCall, runPreviewTool]);

  const previewTemplate = useCallback(
    async (templateId: string) => {
      await runPreviewTool(
        () => previewTemplateCall({ template_id: templateId }),
        "Failed to preview template",
      );
    },
    [previewTemplateCall, runPreviewTool],
  );

  return { blob, error, loading, previewDocument, previewTemplate, clear, setError };
}
