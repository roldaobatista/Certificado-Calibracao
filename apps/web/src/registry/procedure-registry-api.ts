import {
  procedureRegistryCatalogSchema,
  type ProcedureRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadProcedureRegistryCatalogOptions {
  scenarioId?: string;
  procedureId?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadProcedureRegistryCatalog(
  options: LoadProcedureRegistryCatalogOptions = {},
): Promise<ProcedureRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildProcedureRegistryEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.procedureId,
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
    const parsed = procedureRegistryCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildProcedureRegistryEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  procedureId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("registry/procedures", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (procedureId) {
      url.searchParams.set("procedure", procedureId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
