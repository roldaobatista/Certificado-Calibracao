import {
  complaintRegistryCatalogSchema,
  type ComplaintRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadComplaintCatalogOptions {
  scenarioId?: string;
  complaintId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadComplaintCatalog(
  options: LoadComplaintCatalogOptions = {},
): Promise<ComplaintRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildComplaintEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.complaintId,
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
    const parsed = complaintRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildComplaintEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  complaintId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/complaints", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (complaintId) {
      url.searchParams.set("complaint", complaintId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
