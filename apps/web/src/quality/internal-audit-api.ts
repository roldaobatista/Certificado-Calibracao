import {
  internalAuditCatalogSchema,
  type InternalAuditCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadInternalAuditCatalogOptions {
  scenarioId?: string;
  cycleId?: string;
  cookieHeader?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadInternalAuditCatalog(
  options: LoadInternalAuditCatalogOptions = {},
): Promise<InternalAuditCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildInternalAuditEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.cycleId,
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
    const parsed = internalAuditCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildInternalAuditEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  cycleId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/internal-audit", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (cycleId) {
      url.searchParams.set("cycle", cycleId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
