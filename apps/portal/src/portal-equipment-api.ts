import { portalEquipmentCatalogSchema, type PortalEquipmentCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadPortalEquipmentCatalogOptions {
  scenarioId?: string;
  equipmentId?: string;
  apiBaseUrl?: string;
  cookieHeader?: string;
  fetchImpl?: typeof fetch;
}

export async function loadPortalEquipmentCatalog(
  options: LoadPortalEquipmentCatalogOptions = {},
): Promise<PortalEquipmentCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildPortalEquipmentEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.equipmentId,
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
    const parsed = portalEquipmentCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
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

function buildPortalEquipmentEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  equipmentId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("portal/equipment", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (equipmentId) {
      url.searchParams.set("equipment", equipmentId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
