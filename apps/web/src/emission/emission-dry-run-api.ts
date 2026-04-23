import { emissionDryRunCatalogSchema, type EmissionDryRunCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadEmissionDryRunCatalogOptions {
  scenarioId?: string;
  itemId?: string;
  apiBaseUrl?: string;
  cookieHeader?: string;
  fetchImpl?: typeof fetch;
}

export async function loadEmissionDryRunCatalog(
  options: LoadEmissionDryRunCatalogOptions = {},
): Promise<EmissionDryRunCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildEmissionDryRunEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.itemId,
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
    const parsed = emissionDryRunCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildEmissionDryRunEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  itemId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("emission/dry-run", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (itemId) {
      url.searchParams.set("item", itemId);
    }

    return url.toString();
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
