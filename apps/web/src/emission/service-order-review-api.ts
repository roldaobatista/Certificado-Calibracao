import {
  serviceOrderReviewCatalogSchema,
  type ServiceOrderReviewCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadServiceOrderReviewCatalogOptions {
  scenarioId?: string;
  itemId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadServiceOrderReviewCatalog(
  options: LoadServiceOrderReviewCatalogOptions = {},
): Promise<ServiceOrderReviewCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildServiceOrderReviewEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.itemId,
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
    const parsed = serviceOrderReviewCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildServiceOrderReviewEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  itemId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("emission/service-order-review", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (itemId) {
      url.searchParams.set("item", itemId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
