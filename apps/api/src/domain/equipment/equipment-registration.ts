export interface EquipmentRegistrationAddress {
  line1?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

export interface EquipmentRegistrationInput {
  customerId?: string;
  address?: EquipmentRegistrationAddress;
}

export interface EquipmentRegistrationValidation {
  ok: boolean;
  missingFields: string[];
}

export function validateEquipmentRegistration(
  input: EquipmentRegistrationInput,
): EquipmentRegistrationValidation {
  const missingFields: string[] = [];

  if (!isNonEmptyString(input.customerId)) {
    missingFields.push("customerId");
  }

  if (!isNonEmptyString(input.address?.line1)) missingFields.push("address.line1");
  if (!isNonEmptyString(input.address?.city)) missingFields.push("address.city");
  if (!isNonEmptyString(input.address?.state)) missingFields.push("address.state");
  if (!isNonEmptyString(input.address?.postalCode)) missingFields.push("address.postalCode");
  if (!isNonEmptyString(input.address?.country)) missingFields.push("address.country");

  return {
    ok: missingFields.length === 0,
    missingFields,
  };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
