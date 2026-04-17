import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export function useBrand() {
  const { call: getVoiceCall } = useCallTool<string>("get_voice");
  const { call: setVoiceCall } = useCallTool<{ status: string }>("set_voice");
  const { call: getComponentsCall } = useCallTool<string>("get_components");
  const { call: setComponentsCall } = useCallTool<{ status: string }>("set_components");

  const [voice, setVoice] = useState("");
  const [components, setComponents] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [voiceResult, componentsResult] = await Promise.all([
        getVoiceCall({}),
        getComponentsCall({}),
      ]);
      setVoice((voiceResult.data as string) || "");
      setComponents((componentsResult.data as string) || "");
    } catch {
      /* non-critical */
    }
  }, [getVoiceCall, getComponentsCall]);

  const saveVoice = useCallback(
    async (content: string) => {
      await setVoiceCall({ content });
    },
    [setVoiceCall],
  );

  const saveComponents = useCallback(
    async (source: string) => {
      await setComponentsCall({ source });
    },
    [setComponentsCall],
  );

  return { voice, setVoice, components, setComponents, refresh, saveVoice, saveComponents };
}
