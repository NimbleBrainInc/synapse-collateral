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
  const { call: listCall } = useCallTool<DocumentInfo[]>("list_documents");
  const { call: createCall } = useCallTool<WorkspaceState>("create_document");
  const { call: openCall } = useCallTool<WorkspaceState>("open_document");
  const { call: saveCall } = useCallTool<DocumentInfo>("save_document");
  const { call: deleteCall } = useCallTool<string>("delete_document");
  const { call: saveAsTemplateCall } = useCallTool("save_as_template");

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);

  const refresh = useCallback(async () => {
    try {
      const result = await listCall({});
      setDocuments((result.data as DocumentInfo[]) || []);
    } catch {
      /* non-critical */
    }
  }, [listCall]);

  const create = useCallback(
    async (args: { name: string; template_id?: string }): Promise<WorkspaceState> => {
      const result = await createCall(args as Record<string, unknown>);
      return result.data as WorkspaceState;
    },
    [createCall],
  );

  const open = useCallback(
    async (documentId: string): Promise<WorkspaceState> => {
      const result = await openCall({ document_id: documentId });
      return result.data as WorkspaceState;
    },
    [openCall],
  );

  const save = useCallback(
    async (args: Record<string, unknown> = {}): Promise<DocumentInfo> => {
      const result = await saveCall(args);
      return result.data as DocumentInfo;
    },
    [saveCall],
  );

  const remove = useCallback(
    async (documentId: string): Promise<void> => {
      await deleteCall({ document_id: documentId });
    },
    [deleteCall],
  );

  const saveAsTemplate = useCallback(
    async (args: { name: string; description?: string }) => {
      await saveAsTemplateCall(args as Record<string, unknown>);
    },
    [saveAsTemplateCall],
  );

  return { documents, refresh, create, open, save, remove, saveAsTemplate };
}
