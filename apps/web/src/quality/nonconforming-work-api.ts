import {
  nonconformingWorkCatalogSchema,
  type NonconformingWorkCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadNonconformingWorkCatalogOptions {
  scenarioId?: string;
  caseId?: string;
  cookieHeader?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadNonconformingWorkCatalog(
  options: LoadNonconformingWorkCatalogOptions = {},
): Promise<NonconformingWorkCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildNonconformingWorkEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.caseId,
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
    const parsed = nonconformingWorkCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildNonconformingWorkEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  caseId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/nonconforming-work", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (caseId) {
      url.searchParams.set("case", caseId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
