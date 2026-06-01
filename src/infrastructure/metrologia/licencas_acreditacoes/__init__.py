"""Infra do módulo `metrologia/licencas-acreditacoes` (M9 Wave A).

Path aninhado (ADR-0072 — espelha `src/domain/metrologia/licencas_acreditacoes/`).
`DocumentoRegulatorio` é a fonte rica da vigência da acreditação CGCRE (ADR-0079);
o cache `Tenant.acreditacao_vigencia_fim` (lido pelo M8) é sincronizado SÓ via
`aplicar_evento_cgcre`.
"""
