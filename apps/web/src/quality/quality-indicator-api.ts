import {
  qualityIndicatorRegistryCatalogSchema,
  type QualityIndicatorRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadQualityIndicatorCatalogOptions {
  scenarioId?: string;
  indicatorId?: string;
  cookieHeader?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadQualityIndicatorCatalog(
  options: LoadQualityIndicatorCatalogOptions = {},
): Promise<QualityIndicatorRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildQualityIndicatorEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.indicatorId,
  );

  if (!endpoint) {
    return null;
  }

  try {
    const response = await fetchImpl(endpoint, {
      method: "GET",
      headers: {
        accept: "application/json",
        ...(options.cookieHeader ? { cookie: options.cookieHeader } : {}),
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    const parsed = qualityIndicatorRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildQualityIndicatorEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  indicatorId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/indicators", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (indicatorId) {
      url.searchParams.set("indicator", indicatorId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
