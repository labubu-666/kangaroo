import { apiJson } from "./api";

export interface CurrentUser {
  username: string;
  email: string | null;
  avatar_url: string;
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiJson("/api/v1/user", "Failed to fetch user");
}
