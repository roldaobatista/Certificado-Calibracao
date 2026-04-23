import { publicCertificateCatalogSchema, type PublicCertificateCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadPublicCertificateCatalogOptions {
  scenarioId?: string;
  certificateId?: string;
  token?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadPublicCertificateCatalog(
  options: LoadPublicCertificateCatalogOptions = {},
): Promise<PublicCertificateCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildPublicCertificateEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.certificateId,
    options.token,
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
    const parsed = publicCertificateCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildPublicCertificateEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  certificateId?: string,
  token?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("portal/verify", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (certificateId) {
      url.searchParams.set("certificate", certificateId);
    }

    if (token) {
      url.searchParams.set("token", token);
    }

    return url.toString();
  } catch {
    return null;
  }
}
