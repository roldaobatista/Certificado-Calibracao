// @afere/engine-uncertainty — Engine de incerteza de medição
//
// Owner: metrology-calc. Área CRÍTICA (harness/14-verification-cascade.md L4):
// mudança exige full regression + snapshot-diff + property tests (blocker=500 seeds).
//
// Consumo: APENAS por apps/api. Web/Portal/Android não podem importar
// este pacote — violação detectada pelo Gate 6 (packages/ownership-lint).
//
// Implementação real entra na fatia V1 do roadmap (harness/10-roadmap.md).
// Escopo planejado:
// - Combinação de incertezas-tipo A/B em quadratura.
// - Fator de abrangência k=2 (ILAC G8).
// - Regra de decisão com zona de segurança (ILAC G8).
// - Arredondamento conforme DOQ-CGCRE.
// - Property tests cobrindo casos-limite (negativos, zero, infinito, NaN).

export const UNCERTAINTY_ENGINE_VERSION = "0.0.6-indicative-decision-rule";

export {
  buildCertificateMeasurementDeclaration,
  type CertificateMeasurementDeclaration,
} from "./measurement-declarations.js";

export {
  analyzeRawMeasurementData,
  type RawMeasurementAnalysisContext,
  type RawMeasurementAnalysis,
  type RawMeasurementAnalysisInput,
} from "./raw-measurement-analysis.js";

export {
  buildPreliminaryUncertaintyBudget,
  type PreliminaryUncertaintyBudget,
  type PreliminaryUncertaintyBudgetContext,
  type PreliminaryUncertaintyComponent,
  type PreliminaryUncertaintyComponentId,
  type PreliminaryUncertaintyComponentStatus,
} from "./preliminary-uncertainty-budget.js";

export {
  evaluatePortaria157IndicativeTolerance,
  type Portaria157IndicativeToleranceContext,
  type Portaria157IndicativeToleranceEvaluation,
  type Portaria157IndicativePointEvaluation,
} from "./portaria-157-indicative-tolerance.js";

export {
  evaluateIndicativeDecisionRule,
  type IndicativeDecisionEvaluation,
  type IndicativeDecisionMode,
  type IndicativeDecisionPointEvaluation,
  type IndicativeDecisionVerdict,
} from "./indicative-decision-rule.js";
