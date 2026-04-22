import { selfSignupCatalogSchema, type SelfSignupCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadSelfSignupCatalogOptions {
  scenarioId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadSelfSignupCatalog(
  options: LoadSelfSignupCatalogOptions = {},
): Promise<SelfSignupCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildSelfSignupEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
  );

  if (!endpoint) {
    return null;
  }

  try {
    const response = await fetchImpl(endpoint, {
      method: "GET",
      headers: {
        accept: "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    const parsed = selfSignupCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildSelfSignupEndpoint(apiBaseUrl: string, scenarioId?: string): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("auth/self-signup", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
