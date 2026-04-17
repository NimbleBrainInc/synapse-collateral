import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export function useAssets() {
  const listTool = useCallTool<string[]>("list_assets");
  const uploadTool = useCallTool<{ filename: string }>("upload_asset");
  const deleteTool = useCallTool<{ status: string }>("delete_asset");

  const [assets, setAssets] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listTool.call({});
      setAssets((result.data as string[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listTool]);

  const upload = useCallback(
    async (args: { filename: string; base64_data: string }) => {
      await uploadTool.call(args as Record<string, unknown>);
    },
    [uploadTool],
  );

  const remove = useCallback(
    async (filename: string) => {
      await deleteTool.call({ filename });
      setAssets((prev) => prev.filter((x) => x !== filename));
    },
    [deleteTool],
  );

  return { assets, refresh, upload, remove };
}
