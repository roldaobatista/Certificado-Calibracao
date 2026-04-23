import { portalCertificateCatalogSchema, type PortalCertificateCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadPortalCertificateCatalogOptions {
  scenarioId?: string;
  certificateId?: string;
  apiBaseUrl?: string;
  cookieHeader?: string;
  fetchImpl?: typeof fetch;
}

export async function loadPortalCertificateCatalog(
  options: LoadPortalCertificateCatalogOptions = {},
): Promise<PortalCertificateCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildPortalCertificateEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.certificateId,
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
    const parsed = portalCertificateCatalogSchema.safeParse(payload);
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

function buildPortalCertificateEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  certificateId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("portal/certificate", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (certificateId) {
      url.searchParams.set("certificate", certificateId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
