---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: catálogo único de convenções de modelo de domínio transversais (VOs, vigência, soft-delete, FK anonimizável, timezone, moeda, idioma, UUID, soft-cap, NC unificada, ordem garantida cross-entity). Substitui dispersão entre AGENTS.md, REGRAS-INEGOCIAVEIS e ADRs individuais.
relacionados:
  - ADR-0007 (camada domínio + gerador spec→código)
  - ADR-0021 (anonimização vs retenção)
  - ADR-0030 (vigência temporal canônica)
  - ADR-0031 (soft-delete em 3 padrões)
  - ADR-0032 (FK cross-módulo anonimizável)
  - ADR-0033 (idempotência consumer)
  - ADR-0034 (saga + compensação)
  - ADR-0037 (glossário PT-EN canônico)
---

# Modelo de domínio transversal — convenções únicas

> **Pra quê:** evitar que cada Marco/módulo reinvente convenções básicas (vigência, soft-delete, FK PII, timezone, moeda). Antes deste doc, Marco 1 usou `deletado_em`, Marco 2 usou estado-máquina, certificados usaram `revogado_em`, RT usou `encerrado_em` — 4 variantes para 1 conceito. Onda 2-10 do saneamento (2026-05-23) consolida.
>
> **Quem mantém:** Tech-lead. Mudança exige ADR.

---

## 1. Value Objects (VOs) compartilhados

### 1.1. Em `src/domain/shared/value_objects.py`

| VO | Propósito | Validação principal | INV |
|---|---|---|---|
| `Email` | E-mail validado no boundary | RFC 5322 simplificado; lowercase | INV-VALIDACAO-001 |
| `CPF` | CPF Receita Federal | Módulo 11 + rejeita sequência trivial | INV-024 dedup |
| `CNPJ` | CNPJ alfanumérico IN RFB 2.229/2024 | Módulo 11 com mapeamento Serpro | INV-024, INV-036, ADR-0017 |
| `Telefone` | E.164 + DDD-BR ANATEL | Whitelist DDDs válidos; auto-correção sem +55 | (Onda 2) |
| `UF` | Unidade Federativa BR | Whitelist 27 UFs IBGE | (Onda 2) |
| `PaisISO3166` | País alpha-2 | Formato `^[A-Z]{2}$` | (Onda 2) |
| `Dinheiro` | Centavos (int) + moeda ISO 4217 | Aritmética bloqueia mistura de moedas | (Onda 2) |
| `JanelaVigencia` | Vigência canônica | INV-VIG-001..004; datetime tz-aware | ADR-0030 |
| `ReferenciaPIIAnonimizavel` | FK cross-módulo a entidade PII anonimizável | Hash HMAC + key_id versionado | ADR-0032, INV-ANON-001..004 |

### 1.2. Em `src/domain/metrologia/value_objects.py`

| VO | Propósito | Validação principal | INV |
|---|---|---|---|
| `Grandeza` | Enum fechado das grandezas RBC | Whitelist 20 grandezas; PR + revisor RBC pra adicionar | (Onda 2) |
| `FaixaMedicao` | Faixa de medição com unidade | Decimal (não float); unidade whitelist | (Onda 2) |
| `IncertezaExpandida` | Incerteza U + fator k + nível confiança | GUM/JCGM 100; ILAC P14 | cl. 7.6 ISO 17025 |
| `NumeroCertificado` | Sequencial inviolável NIT-DICLA-021 | Formato `<TENANT>-<YYYY>-<NNNNNN>` | INV-034, INV-CER-NUM-001 |

---

## 2. Vigência temporal canônica (ADR-0030)

Toda entidade regulatória temporal tem **4 campos canônicos**:

| Campo | Tipo | Nullable | Semântica |
|---|---|---|---|
| `vigencia_inicio` | `DateTimeField (timestamptz UTC)` | NOT NULL | Quando passou a valer |
| `vigencia_fim` | `DateTimeField (timestamptz UTC)` | NULL = aberta | Quando deixará de valer (planejado) |
| `revogado_em` | `DateTimeField (timestamptz UTC)` | NULL = não revogado | Quando foi revogada antes do fim natural |
| `motivo_revogacao` | `TextField` | NULL salvo se `revogado_em not null` | Motivo (>=10 chars CHECK) |

**Invariantes:** INV-VIG-001..004 em REGRAS-INEGOCIAVEIS.md.
**Hook:** `vigencia-canonica-check.sh` (Onda 4).

---

## 3. Soft-delete em 3 padrões (ADR-0031)

| Padrão | Usar quando | Forma | Exemplos |
|---|---|---|---|
| **A — Estado-máquina** | Ciclo de vida não-trivial com transições audit | `status: CharField(choices=...)` + tabela `<Entidade>EventoStatus` | Equipamento, OS, Atividade, NaoConformidade, Tenant |
| **B — `revogado_em`** | Imutável pós-emissão (WORM regulatório) | Campos ADR-0030 (`vigencia_*` + `revogado_em` + `motivo`) | Certificado, RT, RTCompetencia, EquipamentoVersao, LeituraCorrecao |
| **C — `deletado_em`** | Configuração mutável sem máquina | `deletado_em: DateTimeField(null=True)` + `ClienteAtivosManager` | Cliente, Usuario, Telefone, Procedimento (com vigência), Padrao (com vigência) |

**Invariantes:** INV-SOFT-001..003.
**Hook:** `soft-delete-padrao-check.sh` (Onda 4).
**Tabela entidade→padrão:** ver ADR-0031 §"Tabela entidade → padrão".

---

## 4. FK cross-módulo a entidade PII (ADR-0032)

Toda FK para `Cliente`/`Usuario`/`ResponsavelTecnicoTenant` em entidade Padrão B usa par:

```python
cliente_atual = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
cliente_referencia_hash = models.CharField(max_length=128, null=False)
cliente_referencia_key_id = models.CharField(max_length=32, null=False)
```

`uuid_atual_id == None` = entidade foi eliminada (Zona A ADR-0021).
`hash_original` sempre presente (HMAC-tenant + key_id versionado vN).

**Evento propagador:** `Cliente.Anonimizado` (catálogo v11 — Onda 3).
**Consumers obrigatórios:** `equipamentos`, `certificados`, `os`, `contas-receber`, `comunicacao-omnichannel`.
**Hook:** `fk-pii-anonimizavel-check.sh` (Onda 4).

---

## 5. Timezone (DECISÃO Onda 10)

5.1. **Todo timestamp persiste em `timestamptz` (UTC-aware).** Configuração `USE_TZ = True` + `TIME_ZONE = "America/Sao_Paulo"` em `config/settings/base.py` (já vigente).

5.2. **Entidades metrológicas (Calibração, Padrão, Certificado) acrescentam campo `tz_lab` no nível do tenant** (`Tenant.timezone_laboratorio`, default "America/Sao_Paulo"). Reporte de calibração ISO 17025 cl. 7.7 usa `tz_lab` para hora local do laboratório.

5.3. **VO `JanelaVigencia` exige datetime tz-aware** (INV-VIG-004). Datetime naive levanta `ValueError`.

5.4. **Não há cross-tz operacional V1** — todo cálculo de prazo (LGPD 15 dias, ANPD 3 dias úteis, NF-e SVC) usa UTC com conversão na borda apenas para apresentação.

---

## 6. Moeda (DECISÃO Onda 10)

6.1. **MVP-1 (Wave A) = BRL only.** VO `Dinheiro` aceita parâmetro `moeda` mas valor default é `"BRL"`.

6.2. **V2 = multi-currency.** Quando 1º tenant internacional entrar, ativar:
- `Tenant.moeda_principal` (CharField ISO 4217)
- conversão na borda (não no domínio) — usar cotação salva por dia
- ADR específica para tratamento de conversão fiscal

6.3. **NUNCA usar `float` para dinheiro.** Sempre `Dinheiro(centavos: int, moeda: str)`.

---

## 7. Idioma (DECISÃO Onda 10)

7.1. **MVP-1 = pt-BR canônico.** Certificados, NF-e, UI, notificações.

7.2. **V2 = certificados bilíngues opcionais** (pt + en) para tenants RBC com clientes internacionais. Template separado por idioma; chave técnica em pt-BR (canônica).

7.3. **Decisão diferida para V2 (consultor RBC confirma necessidade — alguns clientes farma exigem cert bilíngue):** ADR específica quando entrar.

---

## 8. UUID (DECISÃO Onda 10)

8.1. **MVP-1 = UUIDv4** (já em uso). Gerado por `uuid.uuid4()` em todos os modelos.

8.2. **V2 = avaliar migração para UUIDv7** (ordenado por tempo — melhor índice em tabelas grandes). Migração custosa; só fazer quando volume justificar.

8.3. **Nenhuma colisão prevista no horizonte** (uuid4 = 122 bits de entropia).

---

## 9. `cliente_canonico_id` vs `cliente.id` (regra de FK)

9.1. **FKs operacionais** (que precisam refletir mescla automática) apontam para `Cliente.id` (com leitura via `resolver_cliente_canonico(id)` que segue cadeia). Exemplo: `OS.cliente`.

9.2. **FKs probatórias** (que precisam preservar identidade no momento do registro) usam `ReferenciaPIIAnonimizavel` com snapshot do `cliente_canonico_id_no_momento_hash` no `*_referencia_hash`. Exemplo: `Certificado.cliente_referencia_hash`.

9.3. **Pós-mescla:** `perdedor.cliente_canonico_id = vencedor.id`; trigger PG bloqueia mudança subsequente (INV-CLI-001).

---

## 10. Pendências e referências

- **Onda 4 saneamento:** hooks `vigencia-canonica-check`, `soft-delete-padrao-check`, `fk-pii-anonimizavel-check` ativos.
- **Onda 5 (Marco 3 OS spec FORWARD):** primeiro consumidor real dessas convenções — verificar se VOs cobrem 100% do cenário.
- **Onda 6:** ADRs 0021, 0024, 0025, 0026, 0027 aceitas (frontmatter atualizado).
- **Onda 9:** GATEs DOM-* todos fechados (`gates-wave-a-consolidado.md`).
- **AGENTS.md §3:** referência cruzada a este documento.

---

## 11. Não-Conformidade (NC) — entidade ÚNICA cross-módulo

11.1. **Existe **uma** entidade `qualidade.NaoConformidade`** — não há `qualidade.NC` separada de `calibracao.NaoConformidade`. Auditoria Onda 1 A-INT-06 detectou drift conceitual em PRDs de Marcos 3 e 4.

11.2. **Módulos consumidores referenciam `qualidade.NaoConformidade.id`** (FK ou hash conforme padrão soft-delete do consumidor). Campos polimórficos `entidade_origem_tipo` + `entidade_origem_id` no `NaoConformidade` apontam quem abriu (calibração, padrão, procedimento, OS, equipamento).

11.3. **INV-INT-013** (ADR-0016) já assume essa unicidade — esta seção apenas crava-a como convenção.

11.4. **Soft-delete:** `NaoConformidade` segue **Padrão A (estado-máquina)** — `status: ABERTA → EM_ANALISE → AÇÃO_CORRETIVA → VERIFICAÇÃO → FECHADA | CANCELADA`. ADR-0031 §"Tabela entidade→padrão".

## 12. Soft-delete entidade → padrão (tabela ampliada)

| Entidade | Padrão | Justificativa |
|---|---|---|
| `Cliente` | C (`deletado_em`) | Cadastro mutável; eliminação efetiva possível (Zona A ADR-0021). |
| `Usuario` | C (`deletado_em`) | Idem. |
| `Equipamento` | A (estado-máquina) | Ciclo de vida complexo (recebido → em_uso → em_calibracao → manutencao → baixado). |
| `EquipamentoVersao` | B (`revogado_em`) | Imutável; versão antiga preservada. |
| `OS` | A | Máquina de estados ADR-0023 + INV-027. |
| `AtividadeDaOS` | A | Estado-máquina ADR-0023 herda. |
| `Certificado` | B | WORM regulatório. |
| `RT` (`ResponsavelTecnicoTenant`) | B | Imutável pós-INSERT (ADR-0022). |
| `RTCompetencia` | B | Idem. |
| `NotaFiscal` | B | Receita imutável; CC-e ou Cancelamento mas não DELETE. |
| `Cobranca` | B | Receita 5a. |
| `NaoConformidade` | A | Ciclo de vida (§11). |
| `Procedimento` (calibração) | C com vigência | Pode ser deprecado; vigência mantida. |
| `Padrao` (metrológico) | C com vigência | Idem. |
| `Tarifa` (pricing) | B | Imutável pós-uso (INV-026). |
| `FeatureFlag` (tenant_features) | C | Configuração mutável. |
| `AuthzPerfil`/`AuthzAcao` | C | Configuração de autorização. |
| `Telefone`/`Endereco` (cliente) | C | Idem. |
| `RecebimentoProvisorio` | A | Estado-máquina (recebido → promovido | descartado). |

Hook `soft-delete-padrao-check.sh` (Onda 4) bloqueia variante 4ª.

## 13. Ordem garantida em operações cross-entity (atende M-INT-03 Onda 1)

13.1. **Mudança em entidade-pai com filhos transacionais** — operação executada em **transação única** com lock pessimista no pai (`SELECT ... FOR UPDATE`) antes de afetar filhos. Eventos publicados via outbox (ADR-0015 fluxo 1 pattern).

13.2. **Cascata cross-módulo via evento** — ordem garantida pelo **handler de cada consumer chamar o próximo evento explicitamente** (ADR-0034 saga orquestrada). Não confiar em ordem de processamento da fila.

13.3. **Caso `BillingSaas.PlanoMudouModulos`** (ADR-0034 §"Ordem garantida cross-módulo"):
1. `billing-saas` publica.
2. `acesso-seguranca` consome → invalida sessões + cache → publica `AcessoSeguranca.SessoesAjustadas`.
3. `feature-flags` consome → atualiza `tenant_features` → publica `Features.Sincronizado`.
4. Módulos consumidores reagem **apenas a `Features.Sincronizado`** (não ao `PlanoMudouModulos` direto).

13.4. **Caso `Cliente.Anonimizado` (ADR-0032 / catálogo v11)** — ordem **não** importa entre os 5 consumers (cada um age em sua FK isoladamente). Idempotência ADR-0033 garante ausência de duplicata.

## 14. Evento `Audit.AcessoCliente` (cross-domínio — M-INT-07 Onda 1)

14.1. **Por quê:** INV-013 manda gravar acesso a dados de cliente em `acessos_dados_cliente`. Eventos cruzando módulos (visão-360°, portal cliente, export LGPD, automação que toca cliente) precisam emitir `Audit.AcessoCliente` para que sink centralize.

14.2. **Schema v1** (catálogo a integrar em `integracoes-inter-modulos.md` Onda 2 derivada):
- `cliente_id`, `cliente_referencia_hash`, `acessor_id_hash`, `motivo` (`visao_360 | portal_cliente | export_lgpd | automacao_<aut_id>`), `finalidade_lgpd`, `dados_acessados[]`, `tenant_id`, `ocorrido_em`.

14.3. **Consumer:** `audit_trail/acessos` grava em `acessos_dados_cliente` (já existente) + emite contagem diária imutável (INV-013-A).

## 15. Módulos que medem uso real (atende M-INT-08 Onda 1)

Lista canônica de módulos que **medem** uso real do cliente para pricing composicional (ADR-0013) ou observabilidade:

| Módulo | Métrica | Unidade | Onde mede | Onde reporta |
|---|---|---|---|---|
| `llm-gateway` (Wave B) | tokens consumidos | int | adapter LLM (porta) | `BillingSaas.UsoMedido` |
| `storage-aferere` | bytes em B2 + bytes em PG | bytes | job diário inventário | `BillingSaas.UsoMedido` |
| `sync-mobile` | bytes sincronizados | bytes | sync engine | `BillingSaas.UsoMedido` |
| `assinatura-a3` (Lacuna) | assinaturas executadas | int | endpoint A3 | `BillingSaas.UsoMedido` |
| `comunicacao-omnichannel` | mensagens enviadas (WhatsApp/SMS/Email) | int | porta `OmniChannelProvider` | `BillingSaas.UsoMedido` |
| `certificados` | certificados emitidos | int | endpoint emissão | `BillingSaas.UsoMedido` |
| `os` | OSes abertas | int | endpoint create | `BillingSaas.UsoMedido` |

Job `medicao-de-uso-diaria` (Wave A) agrega + publica.

## 16. Consumer ghost de Marketplace (M-INT-09 Onda 1)

Módulo `marketplace-extension` (Wave B futuro) é **consumer ghost declarado** — entra como observador read-only de eventos do catálogo (não publica). Ghost preserva contrato: ao virar Wave B, eventos existem e podem ser consumidos sem refactor cross-módulo. Documentado para evitar drift "achei que marketplace pública eventos".

## 17. Como navegar

- Estou criando nova entidade Django → leio §2 (vigência), §3 (soft-delete), §4 (FK PII), §5 (timezone).
- Estou criando VO novo → §1, decido se entra em `shared/` (genérico) ou `metrologia/` (domínio).
- Estou criando endpoint que retorna dinheiro/data → §6 (moeda), §5 (timezone — apresentação UI).
- Estou criando migration retrofit → revisar ADR-0030/0031/0032 + tabela §3.
