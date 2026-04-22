import { portalDashboardCatalogSchema, type PortalDashboardCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadPortalDashboardCatalogOptions {
  scenarioId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadPortalDashboardCatalog(
  options: LoadPortalDashboardCatalogOptions = {},
): Promise<PortalDashboardCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildPortalDashboardEndpoint(
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
    const parsed = portalDashboardCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildPortalDashboardEndpoint(apiBaseUrl: string, scenarioId?: string): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("portal/dashboard", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
