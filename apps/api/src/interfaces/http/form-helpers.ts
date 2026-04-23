export function toBoolean(value: unknown): boolean {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value === "true" || value === "1" || value === "on";
  }

  return false;
}

export function toOptionalString(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function toNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.trim().replace(",", ".");
    if (normalized.length === 0) {
      return undefined;
    }

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : undefined;
  }

  return undefined;
}

export function toDate(value: unknown): Date | undefined {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value;
  }

  if (typeof value !== "string") {
    return undefined;
  }

  const normalized = value.trim();
  if (normalized.length === 0) {
    return undefined;
  }

  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed;
}

export function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .flatMap((entry) => toStringArray(entry))
      .filter((entry): entry is string => typeof entry === "string");
  }

  if (typeof value !== "string") {
    return [];
  }

  return value
    .split(/[\n,;]+/)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

export function toChecklistItems(value: unknown) {
  if (typeof value !== "string") {
    return [];
  }

  return value
    .split(/\r?\n+/)
    .map((entry, index) => {
      const [key, requirementLabel, evidenceLabel, status] = entry.split("|").map((item) => item.trim());
      return {
        key: key || `check-${index + 1}`,
        requirementLabel: requirementLabel ?? "",
        evidenceLabel: evidenceLabel ?? "",
        status: status === "ready" || status === "blocked" ? status : "attention",
      };
    })
    .filter((entry) => entry.requirementLabel.length > 0 && entry.evidenceLabel.length > 0);
}

export function toAgendaItems(value: unknown) {
  if (typeof value !== "string") {
    return [];
  }

  return value
    .split(/\r?\n+/)
    .map((entry, index) => {
      const [key, label, status] = entry.split("|").map((item) => item.trim());
      return {
        key: key || `agenda-${index + 1}`,
        label: label ?? "",
        status: status === "ready" || status === "blocked" ? status : "attention",
      };
    })
    .filter((entry) => entry.label.length > 0);
}

export function toDecisionItems(value: unknown) {
  if (typeof value !== "string") {
    return [];
  }

  return value
    .split(/\r?\n+/)
    .map((entry, index) => {
      const [key, label, ownerLabel, dueDateLabel, status] = entry.split("|").map((item) => item.trim());
      return {
        key: key || `decision-${index + 1}`,
        label: label ?? "",
        ownerLabel: ownerLabel ?? "",
        dueDateLabel: dueDateLabel ?? "",
        status: status === "ready" || status === "blocked" ? status : "attention",
      };
    })
    .filter((entry) => entry.label.length > 0 && entry.ownerLabel.length > 0);
}

export function readRedirectTarget(body: unknown): string | null {
  if (!body || typeof body !== "object") {
    return null;
  }

  const value = "redirectTo" in body ? body.redirectTo : null;
  return typeof value === "string" && value.length > 0 ? value : null;
}

export function isConflictError(error: unknown): boolean {
  return error instanceof Error && /unique|constraint|already exists|duplicate/i.test(error.message);
}
