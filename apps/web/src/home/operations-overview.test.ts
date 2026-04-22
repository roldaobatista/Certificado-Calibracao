import assert from "node:assert/strict";
import { test } from "node:test";

import {
  emissionDryRunCatalogSchema,
  onboardingCatalogSchema,
  selfSignupCatalogSchema,
} from "@afere/contracts";

import { buildOperationsOverviewModel } from "./operations-overview.js";

const SELF_SIGNUP_CATALOG = selfSignupCatalogSchema.parse({
  selectedScenarioId: "signatory-ready",
  scenarios: [
    {
      id: "signatory-ready",
      label: "Signatario pronto",
      description: "Todos os provedores obrigatorios estao habilitados.",
      role: "signatory",
      result: {
        ok: true,
        missingProviders: [],
        mfaRequired: true,
      },
    },
  ],
});

const ONBOARDING_CATALOG = onboardingCatalogSchema.parse({
  selectedScenarioId: "blocked",
  scenarios: [
    {
      id: "blocked",
      label: "Bloqueado por prerequisitos",
      description: "Ainda faltam passos obrigatorios.",
      result: {
        completedWithinTarget: false,
        canEmitFirstCertificate: false,
        blockingReasons: ["primary_signatory_pending", "public_qr_pending"],
      },
    },
  ],
});

const EMISSION_CATALOG = emissionDryRunCatalogSchema.parse({
  selectedScenarioId: "type-b-ready",
  scenarios: [
    {
      id: "type-b-ready",
      label: "Tipo B pronto",
      description: "Todos os gates passam.",
      profile: "B",
      result: {
        status: "ready",
        profile: "B",
        summary: "Dry-run pronto para emissao controlada no perfil B.",
        blockers: [],
        warnings: [],
        checks: [
          {
            id: "profile_policy",
            title: "Politica regulatoria",
            status: "passed",
            detail: "Perfil B compativel com template-b.",
          },
          {
            id: "qr_authenticity",
            title: "QR publico",
            status: "passed",
            detail: "QR autenticado em dry-run com status authentic.",
          },
        ],
        artifacts: {
          templateId: "template-b",
          symbolPolicy: "blocked",
          certificateNumber: "AFR-000124",
          declarationSummary: "Resultado: 149.98 kg | U: +/-0.05 kg | k=2",
          qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-b-001&token=token-b-001",
          qrVerificationStatus: "authentic",
          publicPreview: {
            certificateNumber: "AFR-000124",
          },
        },
      },
    },
  ],
});

test("summarizes the canonical readiness across auth, onboarding and emission", () => {
  const model = buildOperationsOverviewModel({
    selfSignupCatalog: SELF_SIGNUP_CATALOG,
    onboardingCatalog: ONBOARDING_CATALOG,
    emissionCatalog: EMISSION_CATALOG,
  });

  assert.equal(model.readyCount, 2);
  assert.equal(model.blockedCount, 1);
  assert.equal(model.allSourcesAvailable, true);
  assert.equal(model.heroStatusTone, "warn");
  assert.equal(model.cards[0]?.href, "/auth/self-signup?scenario=signatory-ready");
  assert.equal(model.cards[1]?.statusLabel, "Emissao bloqueada");
  assert.equal(model.cards[2]?.statusLabel, "Emissao pronta");
});

test("fails closed when one or more canonical sources are unavailable", () => {
  const model = buildOperationsOverviewModel({
    selfSignupCatalog: null,
    onboardingCatalog: null,
    emissionCatalog: null,
  });

  assert.equal(model.readyCount, 0);
  assert.equal(model.blockedCount, 3);
  assert.equal(model.allSourcesAvailable, false);
  assert.equal(model.heroStatusTone, "warn");
  assert.equal(model.heroStatusLabel, "Revisao operacional necessaria");
  assert.equal(model.cards.every((card) => card.statusLabel === "Sem carga canonica"), true);
});
