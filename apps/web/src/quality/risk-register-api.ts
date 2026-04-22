import {
  riskRegisterCatalogSchema,
  type RiskRegisterCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadRiskRegisterCatalogOptions {
  scenarioId?: string;
  riskId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadRiskRegisterCatalog(
  options: LoadRiskRegisterCatalogOptions = {},
): Promise<RiskRegisterCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildRiskRegisterEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.riskId,
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
    const parsed = riskRegisterCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildRiskRegisterEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  riskId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("quality/risk-register", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (riskId) {
      url.searchParams.set("risk", riskId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
