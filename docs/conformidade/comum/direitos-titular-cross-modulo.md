---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/dados-sinteticos.md
---

# Direitos do titular LGPD — matriz canônica cross-módulo

> **Onda 2 plano-v2 (2026-05-23):** auditor LGPD apontou ⛔ ALTO: "direitos do titular implementados só em `clientes`; OS (Marco 3) tem PII do solicitante; equipamentos pode ter responsável técnico — plano não cobre cross-módulo".
>
> **Pra quê:** LGPD art. 18 garante 9 direitos ao titular. Cada módulo do Aferê que armazena PII tem que atender esses direitos. Esta matriz é a fonte única dizendo COMO cada módulo atende cada direito.

---

## 1. Direitos LGPD art. 18

| Direito (art. 18) | Sigla nesta matriz |
|---|---|
| I — confirmação da existência de tratamento | CONFIRMACAO |
| II — acesso aos dados | ACESSO |
| III — correção de dados incompletos, inexatos ou desatualizados | CORRECAO |
| IV — anonimização, bloqueio ou eliminação de dados desnecessários | ANONIMIZACAO |
| V — portabilidade dos dados | PORTABILIDADE |
| VI — eliminação dos dados tratados com consentimento | ELIMINACAO_CONSENT |
| VII — informação das entidades públicas/privadas com quem o controlador compartilhou | COMPARTILHAMENTO |
| VIII — informação da possibilidade de não fornecer consentimento e consequências | NEGATIVA |
| IX — revogação do consentimento | REVOGACAO |

**Prazo de resposta (LGPD art. 19):** 15 dias úteis a partir da requisição via canal do titular (ADR-0061 reservada, a aceitar na Onda 3).

---

## 2. Matriz por módulo Wave A

Cada célula da matriz indica COMO o módulo atende o direito. Notação:

- ✅ implementado / via endpoint dedicado
- 🛠 implementado via API cross-módulo (`/privacidade/titular/<id>`)
- 🟡 implementado via processo manual com SLA (DPO responde)
- 🔴 não aplicável (módulo não armazena PII desse titular)
- 🚧 pendente da Wave A (placeholder atual)

| Módulo | CONFIRMACAO | ACESSO | CORRECAO | ANONIMIZACAO | PORTABILIDADE | ELIMINACAO_CONSENT | COMPARTILHAMENTO | NEGATIVA | REVOGACAO |
|---|---|---|---|---|---|---|---|---|---|
| **clientes** (M1) | ✅ visão 360 | ✅ export 360 | ✅ PATCH /clientes/{id} | ✅ ADR-0021 zonas A/B/C | ✅ export CSV/JSON | ✅ via anonimização Zona A | 🟡 DPO | ✅ checkbox no cadastro | ✅ endpoint dedicado |
| **equipamentos** (M2) | 🛠 via `/privacidade/titular/<id>` lista equipamentos cujo RT/operador é o titular | 🛠 export agregado | ✅ PATCH /equipamentos/{id} sobre dados do RT | ✅ via `ReferenciaPIIAnonimizavel` (ADR-0032) | 🛠 incluso no export agregado | 🔴 n/a (equipamento mesmo não tem consentimento) | 🟡 DPO | 🔴 n/a | 🔴 n/a (RT é vínculo contratual, não consentimento) |
| **os** (M3) | 🛠 lista OS onde o titular é solicitante / técnico / RT | 🛠 export OS agregado | ✅ via `/clientes/{id}` (solicitante) ou `/usuarios/{id}` (técnico) | 🚧 evento `Cliente.Anonimizado` consumer já existe (Fase 4): UPDATE `OS.cliente_id=NULL` preservando hash | 🛠 incluso no export agregado | 🔴 n/a (OS é contrato de serviço) | 🟡 DPO (revela laboratórios parceiros) | 🔴 n/a | 🔴 n/a |
| **certificados** (M4) | 🛠 lista certificados onde o titular é cliente / RT | 🛠 export agregado | 🔴 imutável pós-emissão (ISO 17025 cl. 7.8) — exceto via errata ADR-0045 | ✅ ADR-0021 Zona C: dados PII no certificado emitido NÃO podem ser anonimizados (retenção regulatória 25a); só anonimização EM LUGAR de cópia operacional | 🛠 PDF/A-3 já é portátil | 🔴 n/a | 🟡 DPO (revela INMETRO/CGCRE compartilhamento) | 🔴 n/a | 🔴 n/a |
| **calibracao** (M4) | 🛠 idem certificados | 🛠 export | 🔴 imutável pós-emissão | ✅ ADR-0021 Zona C | 🛠 export | 🔴 n/a | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **fiscal** (NFS-e) | 🛠 lista NFS-e do titular como tomador | 🛠 export agregado | 🔴 imutável pós-emissão (Receita 5a) — exceto via cancelamento NFS-e quando regra municipal permitir | ✅ ADR-0021 Zona C — anonimização EM LUGAR após período legal | 🛠 PDF/XML é portátil | 🔴 n/a | 🟡 DPO (revela Receita/Município compartilhamento) | 🔴 n/a | 🔴 n/a |
| **contas_receber** | 🛠 lista CR do titular | 🛠 export | ✅ PATCH /clientes/{id} (dados de cobrança) | ✅ via Zona A após quitação + retenção fiscal | 🛠 export | 🔴 n/a (cobrança é contrato) | 🟡 DPO (gateway pagamento) | 🔴 n/a | 🔴 n/a |
| **caixa_tecnico** | 🛠 lista vales/acertos do técnico (titular) | 🛠 export | ✅ PATCH /usuarios/{id} | ✅ após desligamento + retenção CLT/IRPF | 🛠 export | 🔴 n/a (vínculo trabalhista) | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **agenda** | 🛠 lista visitas do técnico | 🛠 export | ✅ PATCH /usuarios/{id} | ✅ propagação via `Cliente.Anonimizado` / `Usuario.Anonimizado` (futuro) | 🛠 export | 🔴 n/a | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **chamados** | 🛠 lista chamados do solicitante / técnico | 🛠 export | ✅ PATCH | ✅ propagação | 🛠 export | 🔴 n/a | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **app_tecnico** | 🛠 lista downloads pelo técnico | 🛠 export | n/a (espelho do servidor) | ✅ TTL 6 meses no cache local + crypto-shredding por chave do tenant (INV-APP-SYNC-001) | n/a (espelho) | 🔴 n/a | 🔴 n/a (cache local) | 🔴 n/a | 🔴 n/a |
| **acesso_seguranca** (módulo) | 🛠 lista acessos PII do titular (modelo `AcessoDadosCliente`) | 🛠 export trilha de acesso | n/a (auditoria imutável) | n/a (auditoria imutável — só hash preservado após anonimização do titular) | 🛠 export | 🔴 n/a | 🛠 lista quem acessou (logs internos) | 🔴 n/a | 🔴 n/a |
| **treinamentos** | 🛠 certificados de treinamento do titular | 🛠 export | ✅ PATCH | ✅ após desligamento + retenção qualidade | 🛠 export | 🔴 n/a | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **seguranca_trabalho** | 🛠 ASOs e EPIs do titular | 🛠 export | ✅ PATCH | ✅ após desligamento + retenção CLT 20a | 🛠 export | 🔴 n/a | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **estoque** | 🔴 n/a (não trata PII) | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| **base_conhecimento** | 🔴 n/a | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| **orcamentos** | 🛠 orçamentos do titular como solicitante | 🛠 export | ✅ via /clientes/{id} | ✅ propagação | 🛠 export | ✅ se ainda não-emitido | 🟡 DPO | 🔴 n/a | 🔴 n/a |
| **licencas_acreditacoes** | 🔴 n/a (atesta laboratório, não PII) | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |

---

## 3. Endpoint canônico cross-módulo

A ADR-0061 (Canal do titular + DPO — reservada, Onda 3 plano-v2) vai criar:

```
GET  /privacidade/titular/{cpf_ou_hash}/acoes
POST /privacidade/titular/solicitar
GET  /privacidade/titular/solicitacoes/{id}
```

Internamente, esse endpoint chama um **fan-out** pelos módulos da matriz §2 cobrindo o tipo de direito solicitado. Cada módulo expõe uma porta `DireitosTitular`:

```python
class DireitosTitularProvider(Protocol):
    def confirmar_tratamento(self, tenant_id: UUID, titular_id_hash: str) -> bool: ...
    def exportar_dados(self, tenant_id: UUID, titular_id_hash: str) -> dict: ...
    def anonimizar(self, tenant_id: UUID, titular_id_hash: str, *, zona: ZonaLGPD) -> AnonimizacaoResultado: ...
```

Cada módulo da matriz com 🛠 implementa esse Protocol. ADR-0021 já cobre a semântica Zona A/B/C.

---

## 4. INV-DIR-TIT-* — invariantes obrigatórias

### INV-DIR-TIT-001 — Toda PII de titular tem ponto de origem rastreável

Toda PII armazenada (CPF, e-mail, telefone, nome, endereço, RG) **tem que** estar associada a uma chave de titular que permite resposta a `/privacidade/titular/{cpf_ou_hash}/acoes`. Tabelas que armazenam PII solta (sem FK para `Cliente`/`Usuario`/`RT`) são proibidas — o auditor `auditor-conformidade-lgpd` valida via inspeção de schema.

### INV-DIR-TIT-002 — Resposta a solicitação em ≤ 15 dias úteis

LGPD art. 19. Watchdog dispara alerta em D+10 (75% do prazo); D+15 chama Roldão (SEV-1). Implementação fica em ADR-0061 (canal do titular).

### INV-DIR-TIT-003 — Resposta inclui motivo quando direito é negado

Quando o direito é `🔴 n/a` ou bloqueado por retenção regulatória, a resposta ao titular cita a base legal específica (LGPD art. 16 / art. 23 / Receita 5a / ISO 17025 8.4 / etc.). Não é aceitável "negado sem justificativa".

### INV-DIR-TIT-004 — RIPD registrado

Toda solicitação gera entrada em `relatorio_impacto_protecao_dados` (RIPD — LGPD art. 38) com: data, titular (hash), direito solicitado, módulos consultados, resposta, prazo cumprido. Retenção do RIPD: 5 anos (ANPD recomendação).

---

## 5. Aplicação à fase atual

| Módulo | Estado atual | Ação cross-módulo necessária |
|---|---|---|
| `clientes` (M1) | Já cobre 8/9 direitos (REVOGACAO consentimento implementado em US-CLI-006) | Adicionar fan-out cross-módulo quando ADR-0061 entrar |
| `equipamentos` (M2) | RT tem PII mas sem endpoint dedicado | Implementar Protocol `DireitosTitularProvider` em retrofit Onda 4 |
| `os` (M3, Fase 5 pendente) | Solicitante tem PII (cliente_canonico_id) | **PRD da Fase 5 deve incluir Protocol `DireitosTitularProvider`** — GATE-DIR-TIT-1 |
| `certificados`, `calibracao`, `fiscal` (M4) | Dados imutáveis pós-emissão | Implementar `confirmar_tratamento` + `exportar_dados` (não `anonimizar` — retenção legal) |
| Outros (Wave A/B) | Não-implementados | Implementar conforme entrar em Wave A |

### GATE-DIR-TIT-1 — Marco 3 Fase 5

PRD do Marco 3 Fase 5 (use cases OS) DEVE incluir seção "Direitos do titular" declarando como OS atende CONFIRMACAO / ACESSO / CORRECAO / ANONIMIZACAO. Hook `prd-direitos-titular-check.sh` (a criar em sub-onda 2C) valida presença.

### GATE-DIR-TIT-2 — Retrofit Marco 1 e Marco 2

Implementar Protocol `DireitosTitularProvider` em `src/infrastructure/clientes/` e `src/infrastructure/equipamentos/`. Entra na Onda 3 plano-v2 junto com ADR-0061 (canal do titular + DPO).

### GATE-DIR-TIT-3 — Endpoint canônico

`/privacidade/titular/*` entra em ADR-0061 (Onda 3 plano-v2).

---

## 6. Como adicionar módulo novo à matriz

Quando módulo novo nasce em Wave A/B:

1. Antes do PRD: identificar qual PII o módulo armazena (regra "comum vs módulo" — `docs/CONVENCOES-DOC.md §4`).
2. PRD declara as 9 células da matriz §2 (linha do módulo).
3. Implementa `DireitosTitularProvider` se há ao menos 1 célula 🛠 ou ✅.
4. Auditor `auditor-conformidade-lgpd` revisa antes de fechar fase.
5. Atualizar esta matriz no mesmo PR.

---

## 7. Não-objetivos desta matriz

- **NÃO** substitui ADR-0021 (anonimização vs retenção — zonas A/B/C). Aquela define O QUE anonimizar; esta define COMO o titular pede.
- **NÃO** substitui ADR-0061 (canal do titular + DPO). Aquela define O ENDPOINT; esta define A MATRIZ.
- **NÃO** cobre dados anônimos agregados (não-PII por definição).
- **NÃO** cobre obrigação de denunciar incidente (LGPD art. 48 — fica em runbook DR + ADR-0019 apólice cyber).
