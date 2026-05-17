---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Licenças e Acreditações

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Acreditação CGCRE | Reconhecimento formal da competência técnica do laboratório pela Coordenação Geral de Acreditação do INMETRO | "certificação CGCRE", "licença CGCRE" | A empresa está autorizada a emitir certificados sob o selo RBC | ISO 17025 + NIT-DICLA-031 |
| RBC | Rede Brasileira de Calibração — selo nos certificados de laboratório acreditado CGCRE | "selo RBC", "RBLE" | Certificado tem reconhecimento oficial INMETRO | INMETRO |
| Escopo da acreditação | Lista oficial de grandezas, faixas e CMC que o laboratório está acreditado a calibrar | "rol acreditado" | Limita o que pode aparecer com selo RBC | NIT-DICLA-031 |
| ART | Anotação de Responsabilidade Técnica — registro junto ao CREA atestando responsabilidade do engenheiro | — | Engenheiro está formalmente responsável | Lei 6.496/77 |
| RRT | Registro de Responsabilidade Técnica — equivalente da ART para arquitetos (CAU) | — | Responsabilidade técnica registrada no CAU | Lei 12.378/10 |
| Certificado digital A1 | Certificado digital instalado em arquivo (software), validade tipicamente 1 ano | "cert A1" | Permite assinatura digital sem token físico | ICP-Brasil |
| Certificado digital A3 | Certificado digital em token/cartão físico, validade tipicamente 1-3 anos | "cert A3", "e-CNPJ A3" | Assinatura exige token conectado | ICP-Brasil + ADR-0009 |
| AC emissora | Autoridade Certificadora que emitiu o certificado digital | "CA" | Identifica quem emitiu (Serasa, Certisign, etc.) | ICP-Brasil |
| Documento bloqueante | Documento que, quando vencido, impede operação dependente (ex: certificado RBC sem acreditação CGCRE) | "doc crítico" | Sistema vai travar se vencer | INV-LIC-001 |
| Modo emergencial | Liberação excepcional de operação com documento vencido, com assinatura A3 do admin e registro auditável | "bypass" (proibido na UI) | Operação executada sob justificativa formal | INV-LIC-002 |
| Renovação | Nova revisão do mesmo documento com nova data de validade | "atualização" | Documento foi prorrogado/recadastrado | INV-022 |
| Vigência | Período entre data emissão e data validade no qual documento tem efeito legal | "validade" (ambíguo) | Documento aceito juridicamente | — |
| Janela de alerta | Conjunto de dias antes do vencimento em que o sistema dispara aviso (90/60/30/15/7) | — | Sistema vai mandar e-mail | — |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → `@deprecated` + janela 3 meses.
- Mudança de definição → bump CHANGELOG.

## Convenções

- PT-BR. Termos legais (ART, RRT, CGCRE) mantidos em sigla oficial.
- Definição em 1 linha. Detalhes em `docs/explicacoes/` quando necessário.
