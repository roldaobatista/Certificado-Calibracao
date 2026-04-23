import { authSessionSchema, type AuthSession } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadAuthSessionOptions {
  apiBaseUrl?: string;
  cookieHeader?: string;
  fetchImpl?: typeof fetch;
}

export async function loadAuthSession(
  options: LoadAuthSessionOptions = {},
): Promise<AuthSession | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildAuthSessionEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  );

  if (!endpoint) {
    return null;
  }

  try {
    const response = await fetchImpl(endpoint, {
      method: "GET",
      headers: buildHeaders(options.cookieHeader),
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    const parsed = authSessionSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildAuthSessionEndpoint(apiBaseUrl: string): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    return new URL("auth/session", normalizedBaseUrl).toString();
  } catch {
    return null;
  }
}

function buildHeaders(cookieHeader?: string) {
  const headers: Record<string, string> = {
    accept: "application/json",
  };

  if (cookieHeader) {
    headers.cookie = cookieHeader;
  }

  return headers;
}
