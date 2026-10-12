// Error responses carry `detail` as a string (domain errors) or a list (validation errors)
async function errorMessage(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((d: { msg: string }) => d.msg).join("; ");
  return fallback;
}

// Sends a request and throws an Error carrying the API's message when it fails
export async function apiFetch(
  path: string,
  fallback: string,
  init?: RequestInit,
): Promise<Response> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await errorMessage(res, fallback));
  return res;
}

export async function apiJson<T>(
  path: string,
  fallback: string,
  init?: RequestInit,
): Promise<T> {
  const res = await apiFetch(path, fallback, init);
  return res.json();
}

// Init for a request with a JSON body
export function jsonBody(method: "POST" | "PATCH", data: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  };
}

export interface Paginated<T> {
  results: T[];
  limit: number;
  offset: number;
  total: number;
}
