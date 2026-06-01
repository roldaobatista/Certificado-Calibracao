---
owner: roldao
revisado_em: 2026-06-01
proximo_review: 2026-09-01
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - ../calibracao/glossario.md
---

# Glossário do módulo Certificados

> Termos específicos. Transversais ficam em `docs/comum/glossario.md`. Termos metrológicos (incerteza, padrão, rastreabilidade) ficam em `../calibracao/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Certificado de calibração | Documento técnico que atesta resultado da calibração de um instrumento | "laudo de calibração" (ambíguo) | Documento principal entregue ao cliente | ISO 17025 7.8 |
| Numeração sequencial | Sequência inviolável por tenant + tipo + ano, sem gaps | — | Auditoria conta a sequência | INV-034 |
| Snapshot | Cópia imutável dos dados no momento da emissão | "fotografia dos dados" | Dados não mudam mesmo se origem mudar | INV-001 |
| Reemissão | Nova versão de certificado já emitido, com link à versão anterior | "reedição", "correção" | Original fica como SUBSTITUIDA, nova é vigente | ISO 17025 7.8.8 |
| Versão SUBSTITUIDA | Versão de certificado anterior à reemissão, visível mas não vigente | "cancelada" (proibido — semântica diferente) | Cliente deve usar a nova | INV-034 |
| Cancelamento | Anulação definitiva de certificado emitido (sem nova versão) | "exclusão" (proibido — não exclui) | Certificado anulado, número não reusa | INV-034 |
| Declaração de conformidade | Manifestação se resultado atende ou não a especificação, considerando regra de decisão | "aprovação" (ambíguo) | Cert diz "conforme" ou "não conforme" | ISO 17025 7.8.6 |
| Regra de decisão | Critério matemático pra declarar conformidade considerando incerteza | — | Texto no certificado explica como decidiu | ILAC G8 |
| RBC | Calibração **acreditada** pela CGCRE (Rede Brasileira de Calibração); só perfil A vigente, com ponto dentro do escopo e `U(ponto) ≥ CMC(ponto)` | "calibração acreditada" (ok); NUNCA usar pra B/C/D | Certificado leva selo RBC; ponto classificado `RBC_OK` | ISO 17025 8.1.3 + ADR-0074/0075 |
| Não-RBC (NAO_RBC) | Resultado **sem** cobertura acreditada — capacidade interna do laboratório (B/C/D) OU perfil A em ponto fora do escopo/vencido/suspenso | "RBC" (proibido — uso indevido de acreditação cl. 8.1.3) | Ponto/cert sem selo RBC; exige ressalva quando decidido pelo RT | ADR-0075 + ILAC-P14 |
| Capacidade interna declarada | Faixa/incerteza que o lab declara executar **sem acreditação RBC** (perfis B/C/D, ou A fora do escopo) | "CMC" (proibido — CMC é só da acreditação A) | Tela mostra "capacidade interna (sem acreditação RBC)" | ADR-0075 cl. 8.1.3 |
| Relatório de Aferição | Documento de perfil **D** (sem as palavras "ISO 17025"/"RBC"/"calibração acreditada") | "certificado de calibração" (proibido pra perfil D) | `Certificado.tipo = RELATORIO_AFERICAO` (materialização Wave A) | matriz-feature-perfil + AC-CER-001-5 |
| Reconciliação (ponto-a-ponto) | Conferência, na emissão, de que cada ponto medido `∈ faixa declarada ⊆ escopo` e `U(ponto) ≥ CMC(ponto)` | "validação" (ambíguo) | `AnaliseReconciliacaoCertificado` + `reconciliacao_hash` no snapshot | ADR-0076 + INV-CER-RECONCILIA-001..005 |
| Ressalva não-RBC | Texto obrigatório no ponto emitido como não-RBC por decisão do RT (anti uso indevido de acreditação) | — | Campo `ressalva_nao_rbc` no snapshot do ponto | INV-CER-RESSALVA-001 + ADR-0075 |
| Validade do certificado | Período recomendado de recalibração (não confundir com validade legal) | "vencimento do cert" | Sugestão — não invalida o resultado | NIT-DICLA |
| Assinatura A3 | Assinatura PKCS#7 com cert digital em token físico, cliente-side | "assinatura eletrônica" (ambíguo) | Validade ICP-Brasil | ADR-0009 |
| PDF/A-1 | Padrão PDF para preservação de longo prazo (≥10 anos) | "PDF" genérico | Documento atende preservação | ISO 19005-1 |
| PDF/UA | Padrão PDF acessível (tags, leitor de tela) | — | Documento acessível WCAG | ISO 14289 |
| Página pública verificadora | URL aberta (sem login) que mostra status do certificado por token opaco | "página de verificação" | QR Code aponta aqui | INV-035 |
| QR Code da etiqueta | Código bidimensional na etiqueta linkando à página pública verificadora | "QR" | Auditor escaneia | — |
| Template de certificado | Estrutura HTML/PDF customizável com variáveis dinâmicas + identidade visual | "modelo" | Visual aplicado ao gerar | — |
| NC (Não Conformidade) | Registro formal de desvio em calibração/serviço, com ação corretiva | "ocorrência" (ambíguo) | Processo qualidade aberto | ISO 17025 7.10 + 8.7 |
| Relatório fotográfico | Documento com fotos antes/depois preservando EXIF (timestamp + geo) | — | Comprovação execução em campo | — |
| Laudo técnico | Parecer técnico avulso assinado pelo RT, fora do escopo de calibração | — | Documento independente | — |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum + calibração.
- Termo deprecado → `@deprecated` + janela 3 meses.
- Mudança de definição → bump CHANGELOG + aviso.

## Convenções

- PT-BR.
- Termos regulados citam norma na coluna Origem.
- 1 linha. Detalhes em `docs/explicacoes/`.
