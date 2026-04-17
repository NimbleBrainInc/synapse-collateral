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
  const listTool = useCallTool<TemplateInfo[]>("list_templates");
  const createTool = useCallTool<TemplateInfo>("create_template");
  const duplicateTool = useCallTool<TemplateInfo>("duplicate_template");
  const deleteTool = useCallTool<string>("delete_template");

  const [templates, setTemplates] = useState<TemplateInfo[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listTool.call({});
      setTemplates((result.data as TemplateInfo[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listTool]);

  const create = useCallback(
    async (args: { template_id: string; name: string; description: string; source: string }) => {
      await createTool.call(args as Record<string, unknown>);
    },
    [createTool],
  );

  const duplicate = useCallback(
    async (args: { template_id: string; new_id: string; new_name: string }) => {
      await duplicateTool.call(args as Record<string, unknown>);
    },
    [duplicateTool],
  );

  const remove = useCallback(
    async (templateId: string) => {
      await deleteTool.call({ template_id: templateId });
    },
    [deleteTool],
  );

  return { templates, refresh, create, duplicate, remove };
}
