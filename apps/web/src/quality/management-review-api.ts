import {
  managementReviewCatalogSchema,
  type ManagementReviewCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadManagementReviewCatalogOptions {
  scenarioId?: string;
  meetingId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadManagementReviewCatalog(
  options: LoadManagementReviewCatalogOptions = {},
): Promise<ManagementReviewCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildManagementReviewEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.meetingId,
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
    const parsed = managementReviewCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildManagementReviewEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  meetingId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/management-review", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (meetingId) {
      url.searchParams.set("meeting", meetingId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
