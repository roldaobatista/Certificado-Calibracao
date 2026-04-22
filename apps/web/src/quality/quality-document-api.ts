import {
  qualityDocumentRegistryCatalogSchema,
  type QualityDocumentRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadQualityDocumentCatalogOptions {
  scenarioId?: string;
  documentId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadQualityDocumentCatalog(
  options: LoadQualityDocumentCatalogOptions = {},
): Promise<QualityDocumentRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildQualityDocumentEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.documentId,
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
    const parsed = qualityDocumentRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildQualityDocumentEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  documentId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/documents", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (documentId) {
      url.searchParams.set("document", documentId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
