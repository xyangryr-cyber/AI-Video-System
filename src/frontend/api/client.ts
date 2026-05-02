export interface ApiError {
  error_code: string;
  message: string;
  status: number;
  details?: unknown;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["content-type"] = "application/json";
  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let parsed: Partial<ApiError> = {};
    try {
      parsed = await res.json();
    } catch {
      /* non-json error */
    }
    const err: ApiError = {
      error_code: parsed.error_code ?? `HTTP_${res.status}`,
      message: parsed.message ?? res.statusText,
      status: res.status,
      details: parsed.details,
    };
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body: unknown) => request<T>("PUT", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
