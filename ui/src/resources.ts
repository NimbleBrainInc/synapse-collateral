import type { useSynapse } from "@nimblebrain/synapse/react";

type Synapse = ReturnType<typeof useSynapse>;

/**
 * Extract resource_link URIs from MCP tool content. The server returns
 * resource_link blocks per the MCP spec; bytes are fetched via
 * synapse.readResource over the ext-apps bridge.
 */
export function extractResourceUris(blocks: unknown[]): string[] {
  return blocks
    .filter(
      (block): block is { type: "resource_link"; uri: string } =>
        block != null &&
        typeof block === "object" &&
        (block as Record<string, unknown>).type === "resource_link" &&
        typeof (block as Record<string, unknown>).uri === "string",
    )
    .map((block) => block.uri);
}

function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

export async function fetchResourceAsBlob(synapse: Synapse, uri: string): Promise<Blob> {
  const result = await synapse.readResource(uri);
  const first = result.contents[0];
  if (!first) throw new Error("No content returned for " + uri);
  const mimeType = first.mimeType ?? "application/octet-stream";
  if (first.blob !== undefined) {
    return new Blob([base64ToBytes(first.blob)], { type: mimeType });
  }
  if (first.text !== undefined) {
    return new Blob([first.text], { type: mimeType });
  }
  throw new Error("Resource has neither blob nor text: " + uri);
}
