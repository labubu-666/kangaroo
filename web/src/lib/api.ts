// Error responses carry `detail` as a string (domain errors) or a list (validation errors)
async function errorMessage(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((d: { msg: string }) => d.msg).join("; ");
  return fallback;
}

const LOGIN_REDIRECTED_AT = "login-redirected-at";
const LOGIN_LOOP_WINDOW_MS = 10_000;

// Sends a request and throws an Error carrying the API's message when it fails
export async function apiFetch(
  path: string,
  fallback: string,
  init?: RequestInit,
): Promise<Response> {
  const res = await fetch(path, init);
  // Not logged in: send the user to the backend login (Dex), which returns to this page.
  // If we just came back from login and still get a 401, the session cookie isn't
  // sticking, so stop instead of looping through Dex again.
  if (res.status === 401) {
    const redirectedAt = Number(
      sessionStorage.getItem(LOGIN_REDIRECTED_AT) ?? 0,
    );
    if (Date.now() - redirectedAt < LOGIN_LOOP_WINDOW_MS) {
      throw new Error("Login did not stick. Check that cookies are enabled.");
    }
    sessionStorage.setItem(LOGIN_REDIRECTED_AT, String(Date.now()));
    const here =
      window.location.pathname + window.location.search + window.location.hash;
    window.location.href = `/auth/login?next=${encodeURIComponent(here)}`;
    throw new Error("Not authenticated");
  }
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

export function jsonBody(
  method: "POST" | "PUT" | "PATCH",
  data: unknown,
): RequestInit {
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
