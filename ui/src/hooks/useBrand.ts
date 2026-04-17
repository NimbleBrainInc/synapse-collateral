import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export function useBrand() {
  const getVoiceTool = useCallTool<string>("get_voice");
  const setVoiceTool = useCallTool<{ status: string }>("set_voice");
  const getComponentsTool = useCallTool<string>("get_components");
  const setComponentsTool = useCallTool<{ status: string }>("set_components");

  const [voice, setVoice] = useState("");
  const [components, setComponents] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [voiceResult, componentsResult] = await Promise.all([
        getVoiceTool.call({}),
        getComponentsTool.call({}),
      ]);
      setVoice((voiceResult.data as string) || "");
      setComponents((componentsResult.data as string) || "");
    } catch {
      /* non-critical */
    }
  }, [getVoiceTool, getComponentsTool]);

  const saveVoice = useCallback(
    async (content: string) => {
      await setVoiceTool.call({ content });
    },
    [setVoiceTool],
  );

  const saveComponents = useCallback(
    async (source: string) => {
      await setComponentsTool.call({ source });
    },
    [setComponentsTool],
  );

  return { voice, setVoice, components, setComponents, refresh, saveVoice, saveComponents };
}
