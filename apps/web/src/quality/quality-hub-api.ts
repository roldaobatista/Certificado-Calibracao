import {
  qualityHubCatalogSchema,
  type QualityHubCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadQualityHubCatalogOptions {
  scenarioId?: string;
  moduleKey?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadQualityHubCatalog(
  options: LoadQualityHubCatalogOptions = {},
): Promise<QualityHubCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildQualityHubEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.moduleKey,
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
    const parsed = qualityHubCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildQualityHubEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  moduleKey?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (moduleKey) {
      url.searchParams.set("module", moduleKey);
    }

    return url.toString();
  } catch {
    return null;
  }
}
