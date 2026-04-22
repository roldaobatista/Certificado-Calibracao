import { offlineSyncCatalogSchema, type OfflineSyncCatalog } from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadOfflineSyncCatalogOptions {
  scenarioId?: string;
  itemId?: string;
  conflictId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadOfflineSyncCatalog(
  options: LoadOfflineSyncCatalogOptions = {},
): Promise<OfflineSyncCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildOfflineSyncEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.itemId,
    options.conflictId,
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
    const parsed = offlineSyncCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildOfflineSyncEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  itemId?: string,
  conflictId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("sync/review-queue", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (itemId) {
      url.searchParams.set("item", itemId);
    }

    if (conflictId) {
      url.searchParams.set("conflict", conflictId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
