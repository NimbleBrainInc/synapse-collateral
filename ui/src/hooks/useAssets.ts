import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export function useAssets() {
  const { call: listCall } = useCallTool<string[]>("list_assets");
  const { call: uploadCall } = useCallTool<{ filename: string }>("upload_asset");
  const { call: deleteCall } = useCallTool<{ status: string }>("delete_asset");

  const [assets, setAssets] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listCall({});
      setAssets((result.data as string[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listCall]);

  const upload = useCallback(
    async (args: { filename: string; base64_data: string }) => {
      await uploadCall(args as Record<string, unknown>);
    },
    [uploadCall],
  );

  const remove = useCallback(
    async (filename: string) => {
      await deleteCall({ filename });
      setAssets((prev) => prev.filter((x) => x !== filename));
    },
    [deleteCall],
  );

  return { assets, refresh, upload, remove };
}
