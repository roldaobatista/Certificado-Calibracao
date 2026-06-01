"""Domínio puro do módulo `metrologia/certificados` (M8 Wave A).

Núcleo metrológico da EMISSÃO do certificado de calibração: reconciliação de
cobertura ponto-a-ponto (`pontos ⊆ declarada` + `U(ponto) ≥ CMC(ponto)`), faixa
efetiva do certificado, snapshots probatórios WORM, máquina de estados. PDF,
assinatura A3, OCSP/TSA, portal e pós-emissão ficam para Wave A (infra externa).

Domínio NÃO importa Django (ADR-0007). Path aninhado `metrologia/certificados/`
(ADR-0072). A tabela física `certificados` permanece achatada em
`infrastructure/certificados/` (contrato trigger INV-025 — ADR-0078).
"""
