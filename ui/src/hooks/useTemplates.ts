import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  page_count: number;
  variables: unknown[];
  created: string;
  modified: string;
}

export function useTemplates() {
  const { call: listCall } = useCallTool<TemplateInfo[]>("list_templates");
  const { call: createCall } = useCallTool<TemplateInfo>("create_template");
  const { call: duplicateCall } = useCallTool<TemplateInfo>("duplicate_template");
  const { call: deleteCall } = useCallTool<string>("delete_template");

  const [templates, setTemplates] = useState<TemplateInfo[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listCall({});
      setTemplates((result.data as TemplateInfo[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listCall]);

  const create = useCallback(
    async (args: { template_id: string; name: string; description: string; source: string }) => {
      await createCall(args as Record<string, unknown>);
    },
    [createCall],
  );

  const duplicate = useCallback(
    async (args: { template_id: string; new_id: string; new_name: string }) => {
      await duplicateCall(args as Record<string, unknown>);
    },
    [duplicateCall],
  );

  const remove = useCallback(
    async (templateId: string) => {
      await deleteCall({ template_id: templateId });
    },
    [deleteCall],
  );

  return { templates, refresh, create, duplicate, remove };
}
