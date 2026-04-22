import assert from "node:assert/strict";
import { test } from "node:test";

import { publicCertificateCatalogSchema } from "@afere/contracts";

import { buildPublicVerificationOverviewModel } from "./public-verification-overview.js";

const CATALOG_FIXTURE = publicCertificateCatalogSchema.parse({
  selectedScenarioId: "authentic",
  scenarios: [
    {
      id: "authentic",
      label: "Certificado autentico",
      description: "Mostra o recorte minimo de metadados para um certificado valido.",
      result: {
        ok: true,
        status: "authentic",
        certificate: {
          certificateNumber: "AFR-000123",
          issuedAtUtc: "2026-04-21T14:00:00Z",
          revision: "R0",
          instrumentDescription: "Balanca IPNA 300 kg",
          serialNumber: "SN-42",
        },
      },
    },
    {
      id: "reissued",
      label: "Certificado reemitido",
      description: "Mostra o relacionamento com a revisao mais recente.",
      result: {
        ok: true,
        status: "reissued",
        certificate: {
          certificateNumber: "AFR-000120",
          reissuedAtUtc: "2026-04-22T08:00:00Z",
          replacementCertificateNumber: "AFR-000120-R1",
          revision: "R1",
          instrumentDescription: "Balanca IPNA 300 kg",
          serialNumber: "SN-42",
        },
      },
    },
    {
      id: "not-found",
      label: "Nao localizado",
      description: "Fluxo fail-closed.",
      result: {
        ok: false,
        status: "not_found",
        reason: "certificate_not_found",
      },
    },
  ],
});

test("summarizes the public verification catalog for the portal home", () => {
  const model = buildPublicVerificationOverviewModel(CATALOG_FIXTURE);

  assert.equal(model.sourceAvailable, true);
  assert.equal(model.authenticCount, 1);
  assert.equal(model.reissuedCount, 1);
  assert.equal(model.notFoundCount, 1);
  assert.equal(model.heroStatusTone, "ok");
  assert.equal(model.featuredScenarioLabel, "Certificado autentico");
  assert.equal(model.cards[1]?.statusTone, "neutral");
  assert.equal(model.cards[2]?.statusLabel, "Sem dados publicos");
});

test("fails closed when the public catalog is unavailable", () => {
  const model = buildPublicVerificationOverviewModel(null);

  assert.equal(model.sourceAvailable, false);
  assert.equal(model.heroStatusTone, "warn");
  assert.equal(model.heroStatusLabel, "Backend obrigatorio");
  assert.equal(model.cards.length, 3);
  assert.equal(model.cards.every((card) => card.statusLabel === "Sem carga canonica"), true);
});
