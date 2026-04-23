import {
  customerRegistryCatalogSchema,
  type CustomerRegistryCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadCustomerRegistryCatalogOptions {
  scenarioId?: string;
  customerId?: string;
  apiBaseUrl?: string;
  cookieHeader?: string;
  fetchImpl?: typeof fetch;
}

export async function loadCustomerRegistryCatalog(
  options: LoadCustomerRegistryCatalogOptions = {},
): Promise<CustomerRegistryCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildCustomerRegistryEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.customerId,
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
    const parsed = customerRegistryCatalogSchema.safeParse(payload);
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

function buildCustomerRegistryEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  customerId?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("registry/customers", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (customerId) {
      url.searchParams.set("customer", customerId);
    }

    return url.toString();
  } catch {
    return null;
  }
}
