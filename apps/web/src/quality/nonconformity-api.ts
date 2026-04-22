import {
  nonconformityRegistryCatalogSchema,
  type NonconformityRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadNonconformityCatalogOptions {
  scenarioId?: string;
  ncId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadNonconformityCatalog(
  options: LoadNonconformityCatalogOptions = {},
): Promise<NonconformityRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildNonconformityEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.ncId,
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
    const parsed = nonconformityRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildNonconformityEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  ncId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/nonconformities", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (ncId) {
      url.searchParams.set("nc", ncId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
