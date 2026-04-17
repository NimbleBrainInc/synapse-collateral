import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export interface DocumentInfo {
  id: string;
  name: string;
  template_id: string | null;
  created: string;
  modified: string;
}

export interface WorkspaceState {
  document_id: string | null;
  document_name: string | null;
  template_id: string | null;
  source: string;
  sections: unknown[];
  has_cache: boolean;
}

export function useDocuments() {
  const listTool = useCallTool<DocumentInfo[]>("list_documents");
  const createTool = useCallTool<WorkspaceState>("create_document");
  const openTool = useCallTool<WorkspaceState>("open_document");
  const saveTool = useCallTool<DocumentInfo>("save_document");
  const deleteTool = useCallTool<string>("delete_document");
  const saveAsTemplateTool = useCallTool("save_as_template");

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listTool.call({});
      setDocuments((result.data as DocumentInfo[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listTool]);

  const create = useCallback(
    async (args: { name: string; template_id?: string }): Promise<WorkspaceState> => {
      const result = await createTool.call(args as Record<string, unknown>);
      return result.data as WorkspaceState;
    },
    [createTool],
  );

  const open = useCallback(
    async (documentId: string): Promise<WorkspaceState> => {
      const result = await openTool.call({ document_id: documentId });
      return result.data as WorkspaceState;
    },
    [openTool],
  );

  const save = useCallback(
    async (args: Record<string, unknown> = {}): Promise<DocumentInfo> => {
      const result = await saveTool.call(args);
      return result.data as DocumentInfo;
    },
    [saveTool],
  );

  const remove = useCallback(
    async (documentId: string): Promise<void> => {
      await deleteTool.call({ document_id: documentId });
    },
    [deleteTool],
  );

  const saveAsTemplate = useCallback(
    async (args: { name: string; description?: string }) => {
      await saveAsTemplateTool.call(args as Record<string, unknown>);
    },
    [saveAsTemplateTool],
  );

  return { documents, refresh, create, open, save, remove, saveAsTemplate };
}
