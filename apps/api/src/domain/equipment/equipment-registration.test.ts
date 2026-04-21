import assert from "node:assert/strict";
import { test } from "node:test";

import { validateEquipmentRegistration } from "./equipment-registration.js";

test("accepts equipment registration when customer and full address are present", () => {
  const result = validateEquipmentRegistration({
    customerId: "customer-1",
    address: {
      line1: "Av. Principal, 100",
      city: "Cuiaba",
      state: "MT",
      postalCode: "78000-000",
      country: "BR",
    },
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.missingFields, []);
});

test("fails closed when customer link is missing", () => {
  const result = validateEquipmentRegistration({
    customerId: "",
    address: {
      line1: "Av. Principal, 100",
      city: "Cuiaba",
      state: "MT",
      postalCode: "78000-000",
      country: "BR",
    },
  });

  assert.equal(result.ok, false);
  assert.deepEqual(result.missingFields, ["customerId"]);
});

test("fails closed when any required address field is absent or blank", () => {
  const result = validateEquipmentRegistration({
    customerId: "customer-1",
    address: {
      line1: "  ",
      city: "Cuiaba",
      state: "",
      postalCode: "78000-000",
      country: "BR",
    },
  });

  assert.equal(result.ok, false);
  assert.deepEqual(result.missingFields, ["address.line1", "address.state"]);
});
