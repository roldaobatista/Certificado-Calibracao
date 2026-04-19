# Consolidação das Análises Críticas do PRD Kalibrium

**Base:** [PRD.md](./PRD.md) (3.814 linhas, 18 seções) · prompt em [PROMPT_ANALISE_PRD.md](./PROMPT_ANALISE_PRD.md)
**Entradas:** duas análises por LLMs distintos seguindo o mesmo prompt (6 papéis: Auditor Cgcre, CTO SaaS, PM sênior, UX/UI, LGPD, Comercial/Founder). Referenciadas aqui como **A1** e **A2**.

---

## Método

Para cada achado: (1) verifiquei no PRD real a citação/linha referenciada; (2) marquei **✅ Confirmado**, **⚠️ Parcial** ou **❌ Impreciso**; (3) consolidei por convergência vs. divergência; (4) priorizei por severidade × custo de não-tratamento.

---

## 1. Convergências fortes (🔴 ambos apontaram — prioridade máxima)

### C1. MVP inchado para 6 meses
- **A1** e **A2** coincidem: §12 Fase 1 (L1047–1071) mistura site PLG, SSO social, multitenancy, 3 perfis A/B/C, 3 templates, wizard de execução completo, engine de incerteza, onboarding 10 passos, billing — sem plano Qualidade completo.
- **✅ Confirmado.** §13 tem 17 critérios de aceite (L1094–1117); §16.3 puxa partes de 17025 (7.7 validade, Qualidade completa) para Fase 2.
- **Risco:** entregar tudo pela metade, errar o coração metrológico.
- **Ação:** cortar para **MVP-0 piloto**: 1 cliente, 1 perfil, sem SSO social, sem billing self-serve — emissão + revisão + assinatura + trilha + sync. PLG e site depois.

### C2. Promessa de conformidade absoluta é risco jurídico/comercial
- **A1** cita slogan "é impossível um certificado sair errado" (Sumário L18) e §2.3 princípio 7 L76 ("impossível, por arquitetura..."). **A2** cita §16.7 L1277–1282 ("100% ... SIM").
- **✅ Confirmado literalmente** em L76 e L1279–1281.
- **Risco:** redação absoluta + §16.2 reconhecendo dependências humanas = peça de contestação em auditoria ou disputa.
- **Ação:** trocar por escopo verificável — "o sistema bloqueia as não conformidades listadas em §9 e impossibilita violação das regras declaradas; conformidade sistêmica 17025 depende da operação". Propagar em §1, §16.7, §17.1 e minuta de contrato.

### C3. Reconciliação offline / idempotência subespecificada
- **A1** e **A2**: §6.3 (L220–226), §7.14 sync e §14 (L1123) tratam sync com "fila persistente, idempotência, reconciliação manual de conflitos" — sem modelo de eventos, matriz de conflitos, locking por agregado.
- **✅ Confirmado.** L1123 literal: "reconciliação manual de conflitos". Não há spec de event sourcing, versionamento por entidade, UNIQUE (device_id, client_event_id), nem política por estado crítico (OS em revisão, assinatura).
- **Risco:** perda/duplicação = certificado errado ou inexistente em categoria regulada.
- **Ação:** criar documento técnico "Modelo de sincronização offline" com event sourcing, idempotência por entidade, optimistic locking, lock exclusivo por OS após início de assinatura, matriz de conflitos com política de merge/rejeição por tipo.

### C4. Base jurídica LGPD + assinatura eletrônica incompletas
- **A1**: DPA/controlador/operador/transferência internacional ausentes; ICP-Brasil fora do MVP (L66, L364) é risco probatório.
- **A2**: papel controlador/operador não documentado; retenção inconsistente (L328 planos vs. L1025 política); direitos do titular vs. imutabilidade não resolvidos.
- **✅ Confirmado.** §11.4 (L1022–1026) tem 5 bullets sem matriz de tratamento; §6.7.1 L354 só lista DPA como item de plano; L364 trata ICP-Brasil como add-on pago de Fase 2.
- **Risco:** cliente corporativo regulado (ANVISA, MAPA, órgão público) não assina; documento probatório questionável em disputa.
- **Ação:** (a) parecer jurídico formal MP 2.200-2 §10 II para assinatura eletrônica; (b) minuta de DPA anexa; (c) matriz `tipo de dado × papel Kalibrium × base legal × retenção × sub-operadores`; (d) declarar região de armazenamento (sa-east-1 ou equivalente BR); (e) fluxo self-service de portabilidade por titular; (f) oferecer ICP-Brasil como add-on opt-in **desde o MVP**.

---

## 2. Convergências médias (🟠 ambos apontaram)

### C5. Tipo A pode emitir sem escopo/CMC completos — contradição interna
- **A1** e **A2** apontam o mesmo: §6.5 L294 diz "Sem esses dados, o perfil A não é ativado", mas §7.14 L779 lista bloqueios duros **apenas** para passos 1, 4, 6, 8 — passo 5 (escopo/CMC) fora. Banner "60% concluído" permite emitir.
- **✅ Confirmado literalmente.**
- **Ação:** fechar a regra — para Tipo A, passos 1, 4, 5, 6, 8 são bloqueio duro. Sem escopo+CMC cadastrados, organização Tipo A não emite certificado acreditado. Atualizar §7.14 L779 e §13 critério 10.

### C6. Wizard de execução é pesado para campo
- Ambos dizem que §7.7 é denso demais; A1 cita meta de 35 min (§3 L88) vs. fragmentação; A2 cita fadiga e pressão de tempo.
- **✅ Confirmado.** §7.7 ocupa L540–674 (135 linhas de spec), vários subpassos.
- **Ação:** reagrupar em 5 macroetapas (Identificação | Padrões+Ambiente | Ensaios | Cálculo+Decisão | Fechamento) com sub-passos em acordeão e checkpoint de "pausar/retomar".

### C7. Audit log imutável precisa hardening real
- **A1** aponta RLS sozinho insuficiente e sugere defesa em camadas; **A2** aponta append-only + hash chain sem WORM, segregação administrativa e checkpoints externos.
- **✅ Confirmado.** §11.3 L1009–1021 e §16.1 L1193 descrevem intenção, mas não hardening operacional.
- **Ação:** §11.3 e §11.6 ganham requisitos explícitos — storage WORM/object lock, checkpoints assinados periodicamente (timestamping), segregação administrativa, prova externa contra insider, fuzz cross-tenant semanal, linter de PR rejeitando SQL sem `organization_id`.

### C8. Posicionamento amplo demais no lançamento
- **A1**: sugere hero use case dominante. **A2**: 3 perfis regulatórios + todas as personas ao mesmo tempo diluem narrativa.
- **✅ Confirmado** contra §1.2 L26–36 e §6.5.
- **Ação:** escolher beachhead. Recomendação convergente: **Tipo B (empresa com padrões rastreáveis, sem acreditação)** — menor risco regulatório, volume maior, ciclo de compra mais curto. Tipo A entra em release dedicado com auditoria simulada Cgcre antes.

### C9. Pricing do Starter frágil
- **A1**: R$249 vs. Excel grátis, sem ROI documentado → baixa conversão.
- **A2**: Starter já inclui Android offline + engine + 3 templates + QR + MFA + portal → custo operacional pode corroer margem.
- **✅ Confirmado.** §6.7.1 L319–355 define pacote pesado; sem §"Economics" com custo por GB/mês.
- **Ação:** (a) calculadora ROI no site; (b) revisar Starter — ou subir preço piso, ou reduzir escopo do Starter; (c) adicionar subseção de unit economics ao PRD (custo S3 + replica + Glacier + PostgreSQL + backup por tenant).

### C10. Dossiê de validação do software ausente
- **A2** crítico: §4.2 L136 mapeia "7.11 Sistemas | Validação interna do próprio sistema", mas §12–§13 não definem protocolo de validação, casos-teste, rastreabilidade requisito→teste, revalidação pós-mudança.
- **✅ Confirmado.** §13 critérios são binários de saída; nenhum entregável "plano de validação".
- **Ação:** criar entregável explícito no MVP — "Plano de Validação do Software Kalibrium", com casos-teste normativos, evidências de execução, aprovação formal e procedimento de revalidação ao mudar a engine.

---

## 3. Achados exclusivos de alto valor

### De A1 (metrologia e engenharia)
- **🟠 "U < CMC bloqueia só o símbolo" é metrologicamente invertido** — §9 L927, L939 (confirmado literalmente).
  U calculado < CMC significa CMC subdeclarada ou balanço com erro. Emitir sem símbolo esconde inconsistência técnica.
  **Ação:** travar certificado até revisão do Gestor da Qualidade, com checkbox "CMC incorreta/subestimada → ação corretiva" ou "erro no balanço → recalcular".
- **🟡 Validação da engine de incerteza** — §7.8 L676–681 e §14 L1122.
  "Seguindo EURAMET cg-18" ≠ "validada". Sem gabarito, regressão passa despercebida e reemissão reaplica o erro via `normative_package` (§16.5).
  **Ação:** ≥10 cenários-referência do próprio cg-18 rodados em CI; release bloqueado se qualquer divergir além de ε declarado. Publicar o conjunto.
- **🟡 Data oficial dependente do relógio do Android** — §7.7.1.
  Dispositivo offline sem NTP = data falha. Data oficial do certificado não pode depender do smartphone.
  **Ação:** guardar timestamp local + NTP; divergência >X horas = flag para revisor; certificado usa data confirmada no servidor.
- **🟡 Métricas §3 vs. §6.7.4 não batem** (✅ confirmado): §3 L84–85 mira 20 labs × 1.500 cert/mês (75 cert/lab/mês); §6.7.4 L385–386 mira MRR R$30k com ARPU R$600 (50 contas). **Ação:** fixar 3 números interdependentes e derivar o resto.
- **🟡 Meta de conversão trial→pago 18%** (L389) é 2x otimista para SaaS B2B regulado. **Ação:** reajustar para 8–10% ano 1; Sales-Assisted para Pro/Enterprise.
- **🟡 Intervalo de recalibração** — L73 já tem escape ("salvo condição contratual específica"). Achado de A1 é redundante com o texto atual. **⚠️ Parcial.**
- **🟡 Normas ausentes** — §4.1 L98–114 não cita NIT-DICLA-026, DOQ-CGCRE-019 (símbolo ILAC MRA), NIT-DICLA-007. **Ação:** ampliar §4.1 e §8.14 Template A com variante de selo combinado Cgcre/ILAC MRA.

### De A2 (produto e exposição pública)
- **🔴 QR público expõe dados além do necessário** — §17.5.6 L2969+ mostra emissor, cliente, item, série, datas, resultado, signatário e oferece "Baixar PDF original" sem autenticação.
  Confidencialidade comercial do cliente do lab pode ser violada; enumeração de hashes é vetor.
  **Ação:** modo público mínimo (autenticidade + status + emissor + metadado essencial); PDF completo e detalhes sob autenticação/autorização; rate limit por hash; anti-enumeração; assinatura de URLs.
- **🟠 Modelo de identidade confuso** — §6.6, §7.1, §7.13, §7.15: e-mail global + membership multi-org + convites + cliente externo + SSO + sugestão por domínio. Mesmo e-mail pode ser interno em uma org e externo em outra.
  **Ação:** separar explicitamente identidades humanas, memberships e atores de portal; documentar troca de contexto e revogação.
- **🟠 Superfície pública cresce rápido** — §7.11 + §17.5 + white-label Enterprise + domínios custom.
  **Ação:** threat model explícito antes do GA.
- **🟠 Prévia integral do certificado no celular é revisão fraca** — passo 13 do wizard.
  **Ação:** resumo crítico com destaque de campos sensíveis; PDF integral como opção.
- **🟠 Reautenticação frequente em campo** — identificação, assinatura do executor, assinatura final + MFA.
  **Ação:** janelas curtas de sessão elevada só para ações de risco.
- **🟡 Critérios de aceite medem saída, não aprendizado** — §13 L1094–1117 (confirmado).
  **Ação:** adicionar métricas de usabilidade/operabilidade: tempo real até 1º certificado, taxa de retorno do revisor, conflitos de sync, abandono por passo.
- **🟠 Governança normativa sem owner no go-live** — §16.6 declara "equipe a constituir junto com lançamento".
  **Ação:** owner nominal + RACI + orçamento antes do piloto pago.

---

## 4. Achados onde as análises divergem (o autor decide)

| Tema | A1 recomenda | A2 recomenda | Recomendação consolidada |
|------|--------------|--------------|--------------------------|
| ICP-Brasil | **opt-in desde o MVP** | não trata diretamente | Opt-in no MVP como add-on pago — cliente regulado pede |
| Regra de decisão (ILAC G8) | não destaca | documentar libraries, wording, banda de guarda | **Adotar A2** — documentar opções suportadas e texto literal que sai no certificado |
| Intervalo de recalibração no certificado | opcional por OS | não trata | PRD já tem escape em L73 — manter como está |
| Engine Android vs. backend | shared lib cross-platform | não trata | **Adotar A1** — ou lib compartilhada, ou backend autoritativo com alerta de divergência >ε |
| Validade dos resultados (7.7 norma) | não destaca | incluir ganchos mínimos no MVP | **Adotar A2** — mínimo: registro de controles e evidências |

---

## 5. Top 10 consolidado (severidade × impacto)

1. 🔴 **MVP inchado** — cortar para piloto controlado (C1)
2. 🔴 **Promessa "100%" / "impossível errar"** — suavizar para escopo verificável (C2)
3. 🔴 **Reconciliação offline subespecificada** — documento técnico dedicado (C3)
4. 🔴 **LGPD DPA + papel controlador/operador + ICP-Brasil** — base jurídica incompleta (C4)
5. 🔴 **QR público expõe PDF completo e dados sensíveis** — reduzir exposição pública (A2)
6. 🔴 **Dossiê de validação do software ausente** — entregável explícito no MVP (C10)
7. 🟠 **Tipo A pode emitir sem escopo/CMC** — contradição §6.5 vs §7.14 (C5)
8. 🟠 **U < CMC bloqueia só símbolo** — regra metrologicamente invertida (A1)
9. 🟠 **Audit log precisa hardening real** — WORM, segregação, checkpoints (C7)
10. 🟠 **Posicionamento amplo demais** — escolher beachhead (C8)

---

## 6. Perguntas que o autor precisa responder antes do código

1. **Beachhead:** qual segmento de entrada — Tipo A, Tipo B ou Tipo C? A recomendação consolidada é **Tipo B**; confirma?
2. **Jurídico:** existe parecer formal MP 2.200-2 para a assinatura eletrônica auditável, e minuta de DPA com matriz controlador/operador?
3. **Validação do software:** qual é o plano de validação (protocolo, casos-teste, aprovação, revalidação)? Onde está documentado?
4. **Engine de incerteza:** qual é o conjunto de cenários-referência EURAMET cg-18 contra o qual a engine é validada em CI?
5. **Sync offline:** há spec de event sourcing, idempotência por entidade e política de conflito por estado crítico? Teste de chaos planejado?
6. **QR público:** o que exatamente fica público (só autenticidade, ou PDF completo)?
7. **Equipe e prazo:** qual o tamanho real do time e o cronograma de 6 meses foi validado bottom-up?
8. **Cliente piloto:** CNPJ, perfil regulatório, volume mensal e disponibilidade para uso diário já estão definidos?
9. **Owner de governança normativa:** quem, com RACI, antes do go-live?
10. **Métricas §3 vs. §6.7.4:** qual é a reconciliação entre as duas tabelas?

---

## 7. Riscos existenciais consolidados

1. **Rejeição em auditoria Cgcre do primeiro cliente Tipo A** — reputação circula por WhatsApp entre gestores da qualidade. **Mitigação:** auditoria simulada com consultor Cgcre externo antes do segundo cliente pago; Tipo A sai depois do Tipo B.
2. **Data breach cross-tenant** — LGPD art.48 + colapso de confiança. **Mitigação:** defesa em camadas (RLS + pool tenant-aware + linter + fuzz semanal) antes de abrir multitenancy real.
3. **Erro sistemático na engine de incerteza** — bug multiplicado por N certificados; reemissão com `normative_package` (§16.5) reaplica o erro. **Mitigação:** gabarito EURAMET em CI é pré-requisito inegociável do MVP.
4. **Promessa comercial superdimensionada gera ação judicial** — "qualquer auditoria", "impossível errar", "passa em qualquer auditoria" no site (§17.1) + erro operacional do cliente. **Mitigação:** claims verificáveis + cláusula contratual clara de limitação.

---

## 8. Plano de ação priorizado (ordem recomendada)

**Antes de qualquer código:**
- [ ] Reduzir escopo MVP: definir MVP-0 (piloto) vs MVP-1 (comercial) em §12
- [ ] Parecer jurídico MP 2.200-2 + minuta DPA + matriz LGPD por tipo de dado
- [ ] Suavizar wording de promessa em §1, §2.3 princípio 7, §16.7, §17.1
- [ ] Escolher beachhead (Tipo B recomendado) e reescrever §6.5 ativação por fase
- [ ] Documento técnico "Modelo de sincronização offline" com event sourcing
- [ ] "Plano de Validação do Software Kalibrium" com casos-teste normativos
- [ ] Conjunto de cenários-gabarito EURAMET cg-18 versionado no repositório
- [ ] Reconciliar §3 com §6.7.4; reajustar meta 18% → 8–10%
- [ ] Fechar contradição §6.5 × §7.14 (Tipo A = passos 1,4,5,6,8 duros)
- [ ] Reescrever regra "U < CMC" em §9 — bloquear revisão, não só símbolo
- [ ] Reduzir exposição do QR público em §17.5.6
- [ ] Definir owner de governança normativa com RACI

**Durante o MVP:**
- [ ] Auditoria simulada Cgcre antes do 2º cliente pago
- [ ] Threat model de superfície pública
- [ ] Testes cross-tenant (linter + pool + fuzz)

---

## Veredito consolidado

**Ambos dizem "ainda não", e com razão.** O PRD é excepcional em profundidade regulatória e arquitetura, e tem ideias fortes (normative_package versionado, 3 perfis A/B/C, reemissão controlada com dupla aprovação, honestidade epistêmica em §16.1 vs. §16.2). Mas não está pronto para implementação sem antes: (1) reduzir o escopo do MVP, (2) fechar base jurídica LGPD e assinatura, (3) especificar sync offline com rigor, (4) produzir o plano de validação do software, (5) resolver contradições internas identificadas, e (6) suavizar a promessa absoluta de conformidade.
