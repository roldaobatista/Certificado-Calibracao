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

export const UNCERTAINTY_ENGINE_VERSION = "0.0.1-scaffold";
