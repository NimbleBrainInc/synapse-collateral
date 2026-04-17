import { useCallback } from "react";
import { useCallTool, useSynapse } from "@nimblebrain/synapse/react";
import { extractResourceUris, fetchResourceAsBlob } from "../resources";

export function useExport() {
  const synapse = useSynapse();
  const exportTool = useCallTool("export_pdf");

  const exportPdf = useCallback(async (): Promise<void> => {
    const result = await exportTool.call({});
    const uris = extractResourceUris(result.content ?? []);
    const pdfUri = uris[0];
    if (!pdfUri) throw new Error("Export returned no resource_link");
    const blob = await fetchResourceAsBlob(synapse, pdfUri);
    const filename = pdfUri.split("/").pop() || "document.pdf";
    synapse.downloadFile(filename, blob, "application/pdf");
  }, [exportTool, synapse]);

  return { exportPdf };
}
