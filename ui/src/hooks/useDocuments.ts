import { useCallback, useState } from "react";
import { useCallTool } from "@nimblebrain/synapse/react";

export interface DocumentInfo {
  id: string;
  name: string;
  template_id: string | null;
  created: string;
  modified: string;
}

export interface DocumentState {
  document_id: string | null;
  document_name: string | null;
  template_id: string | null;
  theme?: {
    colors: Record<string, string>;
    fonts: Record<string, string>;
    spacing: Record<string, string>;
  };
}

/**
 * Document operations bound to the stateless server contract: every
 * write takes ``document_id`` explicitly. There is no implicit cursor.
 */
export function useDocuments() {
  const { call: listCall } = useCallTool<DocumentInfo[]>("list_documents");
  const { call: createCall } = useCallTool<DocumentState>("create_document");
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
    async (args: { name: string; template_id?: string }): Promise<DocumentState> => {
      const result = await createCall(args as Record<string, unknown>);
      return result.data as DocumentState;
    },
    [createCall],
  );

  const save = useCallback(
    async (documentId: string, name?: string): Promise<DocumentInfo> => {
      const args: Record<string, unknown> = { document_id: documentId };
      if (name !== undefined) args.name = name;
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
    async (documentId: string, name: string, description?: string) => {
      const args: Record<string, unknown> = { document_id: documentId, name };
      if (description !== undefined) args.description = description;
      await saveAsTemplateCall(args);
    },
    [saveAsTemplateCall],
  );

  return { documents, refresh, create, save, remove, saveAsTemplate };
}
