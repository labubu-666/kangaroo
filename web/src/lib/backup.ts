import { apiFetch } from "./api";

export const BACKUP_URL = "/api/v1/backup/";

export async function restoreBackup(file: File): Promise<void> {
  const body = new FormData();
  body.append("file", file);
  await apiFetch(`${BACKUP_URL}restore`, "Failed to restore backup", {
    method: "POST",
    body,
  });
}
