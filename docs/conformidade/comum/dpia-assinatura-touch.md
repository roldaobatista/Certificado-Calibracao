---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
ratificacao-oab: pendente (advogado-saas-regulado humano pré-1º tenant externo pago)
relacionados:
  - REGRAS-INEGOCIAVEIS.md (INV-OS-ACEITE-BIO-001)
  - docs/dominios/operacao/modulos/os/modelo-de-dominio.md (AceiteAtividade)
  - docs/conformidade/comum/ripd-os-geolocalizacao.md
  - docs/conformidade/comum/retencao-matriz.md
---

# DPIA — Assinatura touch (traçado manuscrito digital)

> **Relatório de Impacto à Proteção de Dados Pessoais Sensíveis** — LGPD art. 38 + Res. CD/ANPD 4/2023 + ANPD Nota Técnica 2/2023 (biometria comportamental).
>
> **Origem:** NOVO-CRIT-3 da auditoria rodada 2 (2026-05-23). `AceiteAtividade.assinatura_base64` (touch) é dado biométrico LGPD art. 5º II + art. 11 — exige base legal reforçada, chave de criptografia dedicada, e DPIA específica.
>
> **Aprovação requerida:** advogado-saas-regulado humano OAB antes do 1º tenant externo pago.

---

## 1. Identificação

- **Controlador:** o tenant (laboratório/empresa de assistência técnica).
- **Operador:** Aferê (vendor SaaS).
- **Dado tratado:** traçado manuscrito digital ("touch signature") do cliente PF capturado em tela mobile no momento de aceitar atividade de OS.
- **Categorização LGPD:** **dado pessoal sensível — biometria comportamental** (art. 5º II + ANPD NT 2/2023 — "padrões grafomotor identificam o titular além de questões de fato").

## 2. Finalidade

Atender Lei 14.063/2020 art. 4º como assinatura eletrônica simples vinculando manifestação ao signatário. Substitui assinatura em papel quando atendimento é mobile/portal.

## 3. Base legal LGPD

Conflito de bases legais — biometria exige escolha entre:

| Base | Aplicabilidade | Avaliação |
|---|---|---|
| **art. 11 II "a" — consentimento específico e destacado** | Cliente assina explicitamente concordando com captura biométrica | ⚠️ Cliente PF pode revogar — invalida aceite retroativo |
| **art. 11 II "g" — execução de obrigação legal/regulatória** | Lei 14.063 obriga assinatura eletrônica vinculante | ✅ Recomendado — não requer consentimento renovável |
| **art. 11 II "b" — proteção da vida** | Inaplicável | ❌ |
| **art. 11 II "d" — exercício regular de direitos contratuais** | Contrato laboratório↔cliente exige aceite formal | ⚠️ Aceitável mas mais frágil que "g" |

**Decisão Aferê:** combinação **art. 11 II "g"** (Lei 14.063 obriga) + **art. 11 II "a"** (consentimento específico no momento da captura — UX mostra aviso destacado antes do dedo tocar a tela). Dupla âncora protege contra anulação isolada de uma das bases.

## 4. Princípios LGPD aplicados (art. 6º + art. 11)

| Princípio | Aplicação |
|---|---|
| Finalidade | Limitada a prova de manifestação (Lei 14.063). Proibido uso secundário (identificação biométrica, machine learning, marketing). |
| Adequação | Touch signature substitui papel; é meio mais econômico vs ICP-Brasil A3 obrigatório. |
| Necessidade | Apenas quando atividade exige aceite cliente (definido por `tipo_atividade.exige_aceite`). |
| Acesso a dado sensível | Pseudonimização: HMAC dedicado `BIOMETRIA_KEY_*` por tenant (não a KMS geral). |
| Qualidade | Mínimo `len(trajetoria_pontos) ≥ 8` + área bounding box mínima (anti-rabisco vazio). |
| Transparência | UX antes da captura mostra: "Sua assinatura digital é dado biométrico sensível. Ela é gravada de forma cifrada e usada apenas para comprovar sua concordância com esta atividade." |
| Segurança | Criptografia at-rest com chave KMS dedicada (`BIOMETRIA_KEY_*`); TLS em trânsito. |
| Prevenção | Backup cifrado; crypto-shredding ao fim da retenção. |
| Não-discriminação | Falha do touch (cliente sem dedo hábil) → fallback A1 ou aceite presencial com testemunha (`metodo_assinatura=presencial_atendente`). |
| Responsabilização | Audit log de toda captura + acesso (RAT-08 + INV-013). |

## 5. Avaliação de risco

| Risco | Probabilidade | Impacto | Severidade | Mitigação |
|---|---|---|---|---|
| **Vazamento do banco de assinaturas → identificação biométrica** | Baixa | Crítico (LGPD art. 52 + processo de identidade) | **CRÍTICO** | Chave KMS dedicada `BIOMETRIA_KEY_*` distinta da chave geral do tenant; crypto-shredding ao fim retenção |
| **Reuso da assinatura em outro sistema** | Média | Alto | ALTO | Watermark embarcado: cada captura inclui hash do contexto (tenant_id + atividade_id + timestamp) misturado ao traçado antes de cifrar; reuso fora do contexto não passa validação |
| **Coerção do cliente** | Média | Médio (incidência baixa, dano alto se ocorre) | MÉDIO | Direito de revisão humana LGPD art. 20 + canal de denúncia |
| **Assinatura falsa (terceiro pega o dedo do cliente)** | Baixa | Médio | MÉDIO | Combinar com geo + IP hash + (futuro V2) selfie obrigatória |
| **Rabisco vazio aceito como prova** | Alta | Alto | ALTO | Validação `len(trajetoria_pontos) ≥ 8` + bounding box mínima 30×20 px |

## 6. Medidas obrigatórias Wave A

1. **`AceiteAtividade.assinatura_base64` NUNCA armazenada em claro.** Sempre cifrada com `BIOMETRIA_KEY_*` (chave KMS dedicada por tenant) antes de persistir.
2. **Chave KMS dedicada:** `BIOMETRIA_KEY_<tenant_id>` separada de `TENANT_PII_KEY_<tenant_id>` (matriz retenção). Rotação anual + crypto-shredding 5 anos pós-retenção.
3. **Validação mínima:** `len(trajetoria_pontos) ≥ 8` + bounding box ≥ 30×20 px. Falha → retorna `RabiscoInvalido` (400) sem persistir.
4. **Aviso UX destacado** antes da captura — texto canônico em `aceite-atividade-v1.0.md` §4 + popup "Sua assinatura é dado biométrico — leia mais aqui".
5. **Watermark embarcado:** traçado canonicalizado mistura `hash_contexto = HMAC(BIOMETRIA_KEY, tenant_id|atividade_id|aceito_em_iso)` antes de cifrar. Reuso fora do contexto produz hash divergente.
6. **Audit:** toda captura registra `EventoDeOS.tipo=aceite_touch_capturado` com `aceite_atividade_id` + `bbox_area` + `n_pontos` (sem o traçado). Acesso à assinatura cifrada registra `AcessoDadosCliente` (INV-013).
7. **Retenção:** preservada cifrada pelo prazo da atividade pai (5-25a — matriz). Após 5a se atividade não-calibração: substituir traçado por hash + metadata (`bbox_area`, `n_pontos`, `hash_contexto`).
8. **Acesso restrito:** só `papel.admin_tenant + finalidade=defesa_em_juizo` autoriza descriptografia; senão API retorna apenas metadata.

## 7. Direitos do titular (LGPD art. 18)

| Direito | Aplicação |
|---|---|
| Confirmação/Acesso | Cliente vê metadata (data, contexto) no portal; traçado bruto não é exposto rotineiramente |
| Correção | Não aplicável (gestão histórica do fato) |
| Anonimização | Aplicada após 5a se atividade não-calibração — preserva hash, descarta traçado |
| Eliminação | Após retenção mínima (5-25a) — crypto-shredding da chave dedicada |
| Revogação consentimento | Não retroage (art. 8º §5º) — aceite passado mantém validade pela base art. 11 II "g" |

## 8. Decisão de risco residual

**Aprovado para Marco 3 P4 mediante:**

- 8 medidas obrigatórias Wave A implementadas.
- Validação por advogado-saas-regulado humano antes do 1º tenant externo pago.
- `BIOMETRIA_KEY_*` provisionada em AWS KMS MRK antes da 1ª captura touch em produção.
- Hook `biometria-key-validator.sh` (a criar) bloqueia código que tente descriptografar `assinatura_base64` sem `BIOMETRIA_KEY_*` ou sem audit log.

**Risco residual: BAIXO** se as 8 medidas aplicadas; ALTO se faltar qualquer uma.

## 9. Revisão periódica

- Toda mudança em captura/armazenamento de touch → re-aprovação DPIA por advogado.
- Anual: revisar com base em jurisprudência + ANPD.
- Próxima revisão programada: 2027-05-23.
