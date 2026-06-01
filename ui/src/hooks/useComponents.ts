import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export function useComponents() {
  const { call: getComponentsCall } = useCallTool<string>("get_components");
  const { call: setComponentsCall } = useCallTool<{ status: string }>("set_components");

  const [components, setComponents] = useState("");
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getComponentsCall({});
      setComponents((result.data as string) || "");
    } catch {
      /* non-critical */
    } finally {
      setLoading(false);
    }
  }, [getComponentsCall]);

  const save = useCallback(
    async (source: string) => {
      await setComponentsCall({ source });
    },
    [setComponentsCall],
  );

  return { components, setComponents, refresh, save, loading };
}
