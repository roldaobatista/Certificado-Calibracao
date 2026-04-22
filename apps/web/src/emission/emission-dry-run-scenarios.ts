import type { EmissionDryRunResult } from "@afere/contracts";

import {
  buildEmissionDryRunSummary,
  type EmissionDryRunSummaryViewModel,
} from "./emission-dry-run-summary";

type EmissionDryRunScenarioDefinition = {
  label: string;
  description: string;
  result: EmissionDryRunResult;
};

const SCENARIOS = {
  "type-b-ready": {
    label: "Tipo B pronto",
    description: "Todos os gates de emissao controlada passam e o back-office recebe um preview completo do certificado.",
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
          detail: "Perfil B compativel com template-b e simbolo bloqueado.",
        },
        {
          id: "equipment_registration",
          title: "Cadastro do equipamento",
          status: "passed",
          detail: "Cliente e endereco minimo do equipamento preenchidos.",
        },
        {
          id: "standard_eligibility",
          title: "Elegibilidade do padrao",
          status: "passed",
          detail: "Padrao valido, dentro da faixa aplicavel e aceito pelo perfil regulatorio.",
        },
        {
          id: "signatory_competence",
          title: "Competencia do signatario",
          status: "passed",
          detail: "Competencia vigente encontrada para ipna_classe_iii.",
        },
        {
          id: "certificate_numbering",
          title: "Numeracao do certificado",
          status: "passed",
          detail: "Proximo numero reservado em dry-run: AFR-000124.",
        },
        {
          id: "measurement_declaration",
          title: "Declaracao metrologica",
          status: "passed",
          detail: "Resultado: 149.98 kg | U: ±0.05 kg | k=2",
        },
        {
          id: "audit_trail",
          title: "Audit trail da emissao",
          status: "passed",
          detail: "Hash-chain, eventos criticos e metadados de revisao/assinatura consistentes.",
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
        declarationSummary: "Resultado: 149.98 kg | U: ±0.05 kg | k=2",
        qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-b-001&token=token-b-001",
        qrVerificationStatus: "authentic",
        publicPreview: {
          certificateNumber: "AFR-000124",
          issuedAtUtc: "2026-04-22T13:45:00Z",
          revision: "R0",
          instrumentDescription: "Balanca IPNA 300 kg",
          serialNumber: "SN-300-01",
        },
      },
    },
  },
  "type-a-suppressed": {
    label: "Tipo A com simbolo suprimido",
    description: "A emissao segue tecnicamente liberada, mas o back-office deixa claro que o simbolo nao pode aparecer neste ponto.",
    result: {
      status: "ready",
      profile: "A",
      summary: "Dry-run pronto para emissao controlada no perfil A.",
      blockers: [],
      warnings: ["Escopo acreditado fora do ponto ensaiado: simbolo sera suprimido."],
      checks: [
        {
          id: "profile_policy",
          title: "Politica regulatoria",
          status: "passed",
          detail: "Perfil A compativel com template-a e simbolo suprimido.",
        },
        {
          id: "equipment_registration",
          title: "Cadastro do equipamento",
          status: "passed",
          detail: "Cliente e endereco minimo do equipamento preenchidos.",
        },
        {
          id: "standard_eligibility",
          title: "Elegibilidade do padrao",
          status: "passed",
          detail: "Padrao valido, dentro da faixa aplicavel e aceito pelo perfil regulatorio.",
        },
        {
          id: "signatory_competence",
          title: "Competencia do signatario",
          status: "passed",
          detail: "Competencia vigente encontrada para ipna_classe_ii.",
        },
        {
          id: "certificate_numbering",
          title: "Numeracao do certificado",
          status: "passed",
          detail: "Proximo numero reservado em dry-run: CALA-000032.",
        },
        {
          id: "measurement_declaration",
          title: "Declaracao metrologica",
          status: "passed",
          detail: "Resultado: 12.003 kg | U: ±0.08 kg | k=2",
        },
        {
          id: "audit_trail",
          title: "Audit trail da emissao",
          status: "passed",
          detail: "Hash-chain, eventos criticos e metadados de revisao/assinatura consistentes.",
        },
        {
          id: "qr_authenticity",
          title: "QR publico",
          status: "passed",
          detail: "QR autenticado em dry-run com status authentic.",
        },
      ],
      artifacts: {
        templateId: "template-a",
        symbolPolicy: "suppressed",
        certificateNumber: "CALA-000032",
        declarationSummary: "Resultado: 12.003 kg | U: ±0.08 kg | k=2",
        qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-a-001&token=token-a-001",
        qrVerificationStatus: "authentic",
        publicPreview: {
          certificateNumber: "CALA-000032",
          issuedAtUtc: "2026-04-22T10:15:00Z",
          revision: "R0",
          instrumentDescription: "Balanca analitica 32 kg",
          serialNumber: "SN-A-32",
        },
      },
    },
  },
  "type-c-blocked": {
    label: "Tipo C bloqueado",
    description: "Visualiza o comportamento fail-closed quando o perfil nao sustenta a emissao proposta.",
    result: {
      status: "blocked",
      profile: "C",
      summary: "Dry-run bloqueado por 5 verificacoes no perfil C.",
      blockers: [
        "Politica regulatoria do perfil",
        "Cadastro do equipamento",
        "Elegibilidade do padrao",
        "Competencia do signatario",
        "QR publico",
      ],
      warnings: [],
      checks: [
        {
          id: "profile_policy",
          title: "Politica regulatoria",
          status: "failed",
          detail: "Bloqueios: fonte de padrao RBC fora da politica do perfil; texto livre contem termo proibido RBC; texto livre contem termo proibido Cgcre.",
        },
        {
          id: "equipment_registration",
          title: "Cadastro do equipamento",
          status: "failed",
          detail: "Campos ausentes: address.postalCode.",
        },
        {
          id: "standard_eligibility",
          title: "Elegibilidade do padrao",
          status: "failed",
          detail: "Bloqueios: padrao sem certificado valido; padrao fora da faixa aplicavel.",
        },
        {
          id: "signatory_competence",
          title: "Competencia do signatario",
          status: "failed",
          detail: "Bloqueio: competencia nao vigente no momento da assinatura.",
        },
        {
          id: "certificate_numbering",
          title: "Numeracao do certificado",
          status: "passed",
          detail: "Proximo numero reservado em dry-run: LABC-000008.",
        },
        {
          id: "measurement_declaration",
          title: "Declaracao metrologica",
          status: "passed",
          detail: "Resultado: 449.2 kg | U: ±0.12 kg | k=2",
        },
        {
          id: "audit_trail",
          title: "Audit trail da emissao",
          status: "passed",
          detail: "Hash-chain, eventos criticos e metadados de revisao/assinatura consistentes.",
        },
        {
          id: "qr_authenticity",
          title: "QR publico",
          status: "failed",
          detail: "Bloqueio: campos obrigatorios do QR ausentes para o preview.",
        },
      ],
      artifacts: {
        templateId: "template-c",
        symbolPolicy: "blocked",
        certificateNumber: "LABC-000008",
        declarationSummary: "Resultado: 449.2 kg | U: ±0.12 kg | k=2",
        publicPreview: {},
      },
    },
  },
} as const satisfies Record<string, EmissionDryRunScenarioDefinition>;

export type EmissionDryRunScenarioId = keyof typeof SCENARIOS;

export interface EmissionDryRunScenario {
  id: EmissionDryRunScenarioId;
  label: string;
  description: string;
  result: EmissionDryRunResult;
  summary: EmissionDryRunSummaryViewModel;
}

const DEFAULT_SCENARIO: EmissionDryRunScenarioId = "type-b-ready";

export function resolveEmissionDryRunScenario(scenarioId?: string): EmissionDryRunScenario {
  const id = isEmissionDryRunScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
    summary: buildEmissionDryRunSummary(scenario.result),
  };
}

export function listEmissionDryRunScenarios(): EmissionDryRunScenario[] {
  return (Object.keys(SCENARIOS) as EmissionDryRunScenarioId[]).map((scenarioId) =>
    resolveEmissionDryRunScenario(scenarioId),
  );
}

function isEmissionDryRunScenarioId(value: string | undefined): value is EmissionDryRunScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
