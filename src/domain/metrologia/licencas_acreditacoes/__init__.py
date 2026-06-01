"""Domínio puro do módulo `metrologia/licencas-acreditacoes` (M9 Wave A).

Gestão dos documentos regulatórios da EMPRESA (acreditação RBC/CGCRE, licenças,
ART/RRT, certidões): vigência canônica + status calculado + alertas + bloqueio +
histórico WORM + anexo probatório. Fonte rica da vigência da acreditação CGCRE
(ADR-0079) — o cache `Tenant.acreditacao_vigencia_fim` (que o M8 lê) é sincronizado
SÓ via `aplicar_evento_cgcre`. Sem Django (ADR-0007); path aninhado (ADR-0072).
"""
