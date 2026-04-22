import {
  organizationSettingsCatalogSchema,
  type OrganizationSettingsCatalog,
} from "@afere/contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:3000";

export interface LoadOrganizationSettingsCatalogOptions {
  scenarioId?: string;
  sectionKey?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function loadOrganizationSettingsCatalog(
  options: LoadOrganizationSettingsCatalogOptions = {},
): Promise<OrganizationSettingsCatalog | null> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const endpoint = buildOrganizationSettingsEndpoint(
    options.apiBaseUrl ?? process.env.AFERE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    options.scenarioId,
    options.sectionKey,
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
    const parsed = organizationSettingsCatalogSchema.safeParse(payload);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

function buildOrganizationSettingsEndpoint(
  apiBaseUrl: string,
  scenarioId?: string,
  sectionKey?: string,
): string | null {
  try {
    const normalizedBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`;
    const url = new URL("settings/organization", normalizedBaseUrl);

    if (scenarioId) {
      url.searchParams.set("scenario", scenarioId);
    }

    if (sectionKey) {
      url.searchParams.set("section", sectionKey);
    }

    return url.toString();
  } catch {
    return null;
  }
}
