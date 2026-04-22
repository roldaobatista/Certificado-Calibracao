import {
  auditTrailCatalogSchema,
  type AuditTrailCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadAuditTrailCatalogOptions {
  scenarioId?: string;
  eventId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadAuditTrailCatalog(
  options: LoadAuditTrailCatalogOptions = {},
): Promise<AuditTrailCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildAuditTrailEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.eventId,
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
    const parsed = auditTrailCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildAuditTrailEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  eventId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/audit-trail", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (eventId) {
      url.searchParams.set("event", eventId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
