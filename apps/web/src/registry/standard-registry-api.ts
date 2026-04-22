import {
  standardRegistryCatalogSchema,
  type StandardRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadStandardRegistryCatalogOptions {
  scenarioId?: string;
  standardId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadStandardRegistryCatalog(
  options: LoadStandardRegistryCatalogOptions = {},
): Promise<StandardRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildStandardRegistryEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.standardId,
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
    const parsed = standardRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildStandardRegistryEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  standardId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("registry/standards", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (standardId) {
      url.searchParams.set("standard", standardId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
