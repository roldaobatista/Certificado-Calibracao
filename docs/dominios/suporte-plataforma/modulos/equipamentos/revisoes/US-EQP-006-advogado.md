---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-006
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-006.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-006 (recebimento no laboratório / LGPD + ISO 17025 cl. 7.4)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Os templates de aviso UX, texto de notificação e tratamento de exclusão isolada de foto **precisam revisão de advogado humano licenciado** antes do go-live público (fora do MVP-1 dogfooding) porque serão exibidos a milhares de titulares (técnicos, atendentes, clientes finais) e qualquer ambiguidade vira reclamação ANPD.

---

## Veredito

**APROVADO COM RESSALVAS.** O plano está juridicamente sólido na espinha (RAT-EQP-FOTO catalogada, base art. 7º V + ISO 17025 cl. 7.4.4, EXIF strip obrigatório, aviso UX antes da câmera aprovado em E1). As 6 ressalvas abaixo fecham gaps de execução: replicação fiel do aviso E1, qualificação correta da assinatura presencial no termo de devolução, regex anti-PII em `anomalias_observadas`, fluxo de exclusão isolada da foto, template de notificação `contatar_cliente_aguardando` e ajuste de evento `equipamento.anomalia_recebimento` para sanitizar payload.

### Ressalvas (R1–R6)

1. **R1 — Aviso UX antes da câmera E1: replicação literal e versionamento.** O plano cita "aviso UX antes da câmera (RBC B4 / advogado E1)" em T-EQP-062 e no risco 5, mas **não exige cópia literal** do texto aprovado em `revisoes/PRD-advogado.md` §E1 (já cravado em `contratos/ui.md` Tela 6). Recomendação: acrescentar **task explícita** `T-EQP-062a — replicar texto E1 exatamente como está em contratos/ui.md §Tela 6 + persistir `aviso_camera_versao_id` no `EquipamentoRecebimento` (FK pra catálogo de versões de aviso, espelho do `aceite_lgpd_versao_texto` de US-CLI-001 R2)`. Sem versionamento, em 2 anos a ANPD pergunta "qual texto foi exibido ao operador em [data]" e não há resposta. AC novo: `AC-EQP-006-6 — texto do aviso E1 exibido modal-bloqueante antes do botão "abrir câmera"; clique em "Continuar" grava `aviso_camera_aceito_em` + `aviso_camera_versao_id` no recebimento`.

2. **R2 — `termo_devolucao_assinado_url` (assinatura presencial via upload de foto): qualificação Lei 14.063/2020 + cláusulas adicionais.** O plano (T-EQP-066 + risco 6) trata o upload da foto da assinatura física como "presencial via upload pelo almoxarife". Juridicamente isso é uma **assinatura manuscrita digitalizada por terceiro (o almoxarife)**, **não é assinatura eletrônica simples (Lei 14.063/2020 art. 4º I)** — a Lei 14.063 trata da assinatura *do próprio signatário* via meio eletrônico. O upload da foto da assinatura física pelo almoxarife é prova documental sob CPC art. 411 III (documento particular assinado), com valor de princípio de prova escrita; vale entre as partes, mas é mais fraca que art. 4º I.
   - **Recomendação operacional:**
     - Renomear campo na UI/contrato: "Comprovante de devolução assinado (foto)" — evitar a palavra "assinatura eletrônica".
     - Persistir 4 campos juntos: `termo_devolucao_foto_url` + `termo_devolucao_assinado_por_nome` (texto livre — quem assinou fisicamente) + `termo_devolucao_assinado_por_documento` (CPF/RG opcional — só se cliente concordar) + `termo_devolucao_testemunha_usuario_id` (almoxarife que registrou a entrega). Hash + carimbo do tempo no upload (audit).
     - Texto PT-BR do termo (gerado em PDF antes da impressão pra assinatura física):
       > "Declaro ter recebido em devolução o equipamento TAG **[TAG]** (NS **[NS]**, fabricante **[FAB]**, modelo **[MOD]**), em **[data/hora]**, na condição visual abaixo registrada e com as fotos anexas. **[Razão Social do Tenant]** é responsável pela calibração realizada conforme certificado emitido (quando houver). Esta devolução não substitui o certificado de calibração nem comprovantes fiscais aplicáveis."
       > Assinatura do recebedor: _______________________
       > Nome legível: ____________________ — Documento (opcional): _______
       > Almoxarife responsável pela entrega: _______ (matrícula tenant).
     - **Quando portal-cliente entrar (Wave B):** migrar pra assinatura eletrônica simples (Lei 14.063/2020 art. 4º I) com clique + IP hash + timestamp + texto versionado — aí sim cabe a base legal correta. Documentar essa migração como débito conhecido em `non-goals`.

3. **R3 — `anomalias_observadas` (text livre) sem regex anti-PII = espelho exato do gap `localizacao_fisica` (INV-EQP-LOC-001).** O plano define `anomalias_observadas` como text livre (T-EQP-064, modelo §EquipamentoRecebimento linha 92) e **não aplica validação anti-PII**. Almoxarife sob pressão pode escrever "cliente João Silva CPF 123.456.789-00 reclamou que veio amassado" — gera PII em campo que vai pra audit, evento, eventual export pra cliente. Recomendação: aplicar **regex anti-PII idêntico ao de `localizacao_fisica`** (CPF, CNPJ, e-mail, telefone, nomes capitalizados ≥2 palavras consecutivas), limite 1000 chars, mensagem de erro clara. Criar **`INV-EQP-ANOM-001` — `anomalias_observadas` validada anti-PII no save + endpoint rejeita 400**. Tasks novas:
   - `T-EQP-069a — testes: test_anomalias_observadas_com_cpf_retorna_400, test_anomalias_observadas_com_email_retorna_400, test_anomalias_observadas_limpo_201`.
   - Aviso UX abaixo do textarea (texto pronto):
     > "Descreva apenas o estado físico do equipamento (ex.: *'lacre violado na base, amassado na lateral direita'*). **Não inclua nome, CPF, e-mail ou telefone do cliente** — esses ficam no cadastro do cliente. Limite: 1000 caracteres."
   - Análogo deve ser aplicado a `justificativa_decisao` (text ≥30 chars) — mesmo risco, mesma regra: `INV-EQP-ANOM-002`.

4. **R4 — Exclusão isolada da foto (direito do titular incidentalmente capturado) sem fluxo definido.** A revisão PRD §B4 item 4 cravou "Política de exclusão isolada da foto (audit do delete preservado)" e item 5 deu prazo "15 dias úteis (canal LGPD do tenant)". O plano US-EQP-006 **não tem task** pra esse fluxo. Sem isso, quando o funcionário fotografado por engano pedir exclusão, o almoxarife não terá ferramenta operacional — pedido vai morar em e-mail informal. Recomendação:
   - **Task nova `T-EQP-070 — endpoint `DELETE /v1/equipamentos/{id}/recebimentos/{rid}/fotos/{foto_id}` com `motivo` (enum: `solicitacao_titular_lgpd | erro_operacional | duplicada`) + `justificativa` (≥30 chars) + `solicitante_referencia` (texto opaco, NÃO o nome em claro — referência tipo ticket interno)`. Authz: metrologista + admin (almoxarife NÃO — gatilho de governança).**
   - Comportamento: foto é apagada do Backblaze B2 (binary) **mas o registro fica** com `url=NULL`, `excluida_em`, `excluida_motivo`, `excluida_por_usuario_id`, `excluida_justificativa` (audit imutável). Hash original preservado pra audit.
   - **Restrição ISO 17025:** se a foto for **a única evidência de condição visual** em perfil A e a exclusão deixar o recebimento sem foto, sistema retorna **409** com mensagem "exclusão criaria não-conformidade ISO 17025 cl. 7.4.4 — substitua por outra foto antes ou registre não-conformidade formal" (espelho do cenário `retencao-matriz.md` Cenário E + DRILL-RET-10).
   - **Alternativa preferida (V2):** anonimização (blur facial server-side) em vez de exclusão — preserva evidência ISO 17025 + atende direito do titular. Marco 2 entrega exclusão isolada com guard ISO; blur fica V2.
   - Evento: `equipamento.foto_recebimento_excluida` (payload sanitizado — apenas `equipamento_id`, `recebimento_id`, `foto_id_hash`, `motivo`, `por_usuario_id`).
   - AC novo: `AC-EQP-006-7 — endpoint DELETE de foto opera com guard ISO 17025 (409 se ficaria sem evidência em perfil A); audit imutável preserva ato de exclusão`.

5. **R5 — Template PT-BR da notificação `contatar_cliente_aguardando` + base legal + canal.** O plano (T-EQP-064 + AC-EQP-006-2 do PRD) dispara `NotificacaoClienteService.notificar_anomalia_recebimento()` quando `decisao_apos_anomalia=contatar_cliente_aguardando`, **mas não tem texto pronto**. Marco 2 adapter é `EmptyNotificacaoClienteService` (loga warning — `comunicacao-omnichannel` ainda não existe), então o evento `equipamento.anomalia_recebimento` é o que vai pro audit; texto entra quando módulo de comunicação aterrissar. Mesmo assim, **o template precisa estar cravado agora** (versionamento legal — espelho R1) pra evitar reescrita ad-hoc no Wave B.
   - **Base legal:** Aferê é operador; tenant é controlador. Notificação ao cliente final é tratamento sob art. 7º V (execução de contrato do tenant ↔ cliente final) — não é marketing, não exige opt-in separado. Canal: o que o cliente cadastrou (e-mail/SMS/WhatsApp conforme preferência salva em `Cliente.canal_preferido` — Wave A clientes).
   - **Texto sugerido (PT-BR, ≤120 palavras, espelho tom calmo):**
     > **Assunto:** Recebemos seu equipamento — precisamos da sua confirmação antes de calibrar
     >
     > Olá, **[nome do cliente]**.
     >
     > Recebemos no laboratório o equipamento **[TAG]** (**[fabricante] [modelo]**, NS **[NS]**) em **[data/hora]**. Durante a inspeção visual de entrada identificamos: *"**[anomalias_observadas — saneado de PII]**"*.
     >
     > Antes de prosseguir com a calibração, **precisamos da sua confirmação** sobre como continuar. Por favor, responda a este contato ou ligue para **[telefone do tenant]** — sua resposta é necessária para que o serviço siga conforme contratado.
     >
     > Caso prefira a devolução do equipamento sem calibração, também podemos providenciar.
     >
     > Atenciosamente,
     > **[Razão Social do Tenant]** — Laboratório de Calibração
     >
     > *Esta mensagem refere-se à execução do serviço contratado por você (Lei 13.709/2018 art. 7º, V).*
   - **Justificativa do template:**
     - Cita o **tenant** como remetente (operador = Aferê, controlador = tenant — RAT-EQP-FOTO + RAT-03).
     - Reproduz `anomalias_observadas` **saneado** (regex anti-PII R3 já garantiu que não tem CPF/nome de terceiro lá).
     - Cita base legal art. 7º V no rodapé (transparência, art. 6º VI).
     - **NÃO inclui marketing** (vedação art. 8º §4º LGPD — bundle).
     - Oferece **alternativa de devolução** — defesa contratual do tenant (cliente não pode reclamar depois que "calibraram sem perguntar").
   - **Task nova `T-EQP-071 — criar template versionado em `src/templates/equipamentos/notificacao_anomalia_recebimento_pt_br.md` + entrada no catálogo `docs/conformidade/comum/templates-comunicacao.md` (a criar se não existir) + campo `notificacao_anomalia_template_versao_id` no `EquipamentoRecebimento` (gravado quando notificação dispara)`.**
   - AC novo: `AC-EQP-006-8 — texto da notificação é versionado; payload do evento `equipamento.anomalia_recebimento` carrega `template_versao_id` quando `decisao=contatar_cliente_aguardando``.

6. **R6 — Payload do evento `equipamento.anomalia_recebimento` precisa sanitização explícita.** Modelo-de-domínio §Eventos linha 234 define payload `{ equipamento_id, recebimento_id, anomalia, decisao }`. Linha 238 instrui "Não logar em payload: NS em claro, nome/CPF/CNPJ/e-mail/telefone cliente em claro, localização_fisica". Mas `anomalia` no payload corresponde a `anomalias_observadas` — campo text livre que (mesmo com R3 ativo) pode escapar regex em corner cases. Recomendação:
   - Renomear campo do payload: `anomalia_hash` (HMAC-SHA256 salgado por tenant — espelho do tratamento de PII em `clientes`) + `anomalia_categoria` (enum derivado do `condicao_visual_chegada`: amassado/lacre_violado/contaminado/etc).
   - Payload final do evento: `{ equipamento_id, recebimento_id, anomalia_categoria, anomalia_hash, decisao, template_versao_id? }`.
   - **Task nova `T-EQP-064a — sanitizador de payload em `src/application/equipamentos/eventos.py` que gera hash salgado + categoria antes de publicar o evento`.**
   - Teste novo: `test_evento_anomalia_recebimento_nao_vaza_texto_livre_em_claro`.

### Não-ressalvas (validadas como corretas)

- ✅ **Base legal RAT-EQP-FOTO (art. 7º V + ISO 17025 cl. 7.4.4 + art. 11 §4º se rosto identificável)**: catalogada corretamente em `lgpd-rat.md` linha 50. Plano respeita ao tornar foto obrigatória em A + aviso UX (R1) + EXIF strip + blur diferido pra V2.
- ✅ **EXIF strip obrigatório (Pillow sem `_getexif()` — T-EQP-062)**: correto. Defende contra metadados GPS/dispositivo do funcionário (RAT-13 traz risco análogo no app técnico — aqui é menos crítico porque foto sai de tablet do laboratório, mas tratamento idêntico).
- ✅ **Foto obrigatória só em perfil A**: correto. ISO 17025 cl. 7.4.4 exige "registro de condição de chegada"; perfil A é o único acreditado/declarado-rastreável e responde por NC formal; B/C/D fazem foto opcional pra reduzir atrito.
- ✅ **Máquina de estados ≥6 fases com trigger PG (T-EQP-061)**: do ponto de vista jurídico-regulatório, atende rastreabilidade exigida por ISO 17025 cl. 7.4 + LGPD art. 6º V (qualidade). Trigger PG impede UPDATE manual em audit imutável.
- ✅ **`condicao_visual_chegada` como enum fechado + `decisao_apos_anomalia` enum fechado**: correto. Enum fechado reduz superfície de ambiguidade e vazamento de PII (vs text livre).
- ✅ **Storage local em dev + porta `FotoStorageService` com adapter dev/stub (T-EQP-063)**: correto. Empty adapter em prod proibido via `port-binding-validator`.

---

## Análise por área

### LGPD / Privacidade

- **Papel correto:** Aferê = operador; tenant = controlador da foto do equipamento e da notificação ao cliente final. RAT-EQP-FOTO + RAT-03 cobrem.
- **Base legal default:** art. 7º V (execução de contrato tenant↔cliente final) + ISO 17025 cl. 7.4.4 reforça (obrigação regulatória, art. 7º II) quando perfil A. Rosto identificável incidental ativa art. 11 §4º (sensível) — anonimização (blur) ou exclusão sob pedido cobre.
- **Dados PII em campos texto livre:** `anomalias_observadas` + `justificativa_decisao` sem regex anti-PII é o gap operacional mais grave deste plano (R3). Sem fechar, INV-EQP-LOC-001 vira regra decorativa enquanto outros campos texto vazam livre.
- **Direito de exclusão isolada (art. 18 IV):** Marco 2 entrega via R4. Blur facial fica V2.
- **Retenção:** vigência do equipamento + 5 anos pós-sucateamento; 25 anos quando compõe evidência ISO 17025 cl. 7.4.4. Crypto-shredding por tenant.

### Contratual

- **DPA tenant↔Aferê** já tem cláusula RAT-EQP-FOTO em draft (`revisoes/PRD-advogado.md` §D3) — confirmar inclusão no template de DPA.
- **Termo de devolução (R2):** valor jurídico de documento particular CPC art. 411 III + boa prática civil; quando portal-cliente entrar (Wave B), migra pra Lei 14.063/2020 art. 4º I (eletrônica simples) corretamente qualificada.
- **Recusa de devolver (`decisao=recusar_devolver`):** ato unilateral do tenant — base contratual é o contrato de prestação de serviço; o sistema deve gravar **justificativa ≥30 chars** (já no plano) e produzir notificação ao cliente final (R5 cobre via mesmo template, ajustando frase final).

### Regulatório (ISO 17025 + ANPD)

- **ISO 17025 cl. 7.4.4 + 7.4.5:** condição visual de chegada + registro + rastreabilidade até devolução — atendido pelo `EquipamentoRecebimento` + máquina de estados + fotos.
- **Res. CD/ANPD 15/2024:** se vazar foto com rosto identificável, tenant comunica ANPD em ≤3 dias úteis; Aferê comunica tenant em ≤24h (DPA). INV-005 cobre.
- **Res. CD/ANPD 18/2024 (DPO):** página `/{tenant_slug}/lgpd` (US-CLI-001 R4) é o canal de exercício de direitos — incluir link do "como excluir foto" lá quando R4 entregar.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aviso UX antes da câmera versionado sem registro de qual versão foi exibida — ANPD pergunta "qual texto operador viu em [data]" | Alta sem R1 | Multa ANPD + NC RBC | R1 — `aviso_camera_versao_id` + `aviso_camera_aceito_em` no recebimento |
| Almoxarife sob pressão escreve PII em `anomalias_observadas` (CPF/nome cliente) — vaza pra audit, evento e eventual export | Alta sem R3 | Multa ANPD (2% faturamento) + ressentimento cliente | R3 — regex anti-PII + INV-EQP-ANOM-001 + aviso UX abaixo do textarea |
| Foto de funcionário capturada incidentalmente sem fluxo de exclusão — pedido morre em e-mail | Média | NC LGPD art. 18 IV + reclamação ANPD + risco trabalhista (assédio digital) | R4 — endpoint DELETE com guard ISO + audit imutável + V2 blur |
| `termo_devolucao_assinado_url` rotulado como "assinatura eletrônica simples" sem cumprir Lei 14.063/2020 (não foi o titular que clicou) | Média | Termo perde valor probatório + cliente alega não ter assinado | R2 — renomear UI/contrato + persistir 4 campos + texto do termo cravado |
| Notificação `contatar_cliente_aguardando` escrita ad-hoc pelo módulo `comunicacao-omnichannel` quando aterrissar — texto inconsistente, possível bundle de marketing | Alta sem R5 | NC LGPD art. 8º §4º (bundle) + ressentimento titular | R5 — template versionado + AC-EQP-006-8 |
| Payload do evento `equipamento.anomalia_recebimento` carrega texto livre `anomalia` — vaza PII apesar de regex (corner case escapou) | Média sem R6 | Audit imutável fica com PII em claro = NC permanente | R6 — sanitizador hash+categoria + teste de não-vazamento |
| Crypto-shredding na Wave B esquece `termo_devolucao_assinado_por_documento` (CPF opcional) | Média | Resíduo PII pós-exclusão | Comentário no modelo + checklist Wave B (espelho US-CLI-001 R5) |

---

## Próximos passos

- ✅ Aplicar R1–R6 no plano `US-EQP-006.md` (autoria: implementador / tech-lead).
- ✅ Acrescentar `INV-EQP-ANOM-001` e `INV-EQP-ANOM-002` em `REGRAS-INEGOCIAVEIS.md` (espelho INV-EQP-LOC-001).
- ✅ Criar template `src/templates/equipamentos/notificacao_anomalia_recebimento_pt_br.md` + entrada em `docs/conformidade/comum/templates-comunicacao.md` (criar arquivo se não existir).
- ✅ Acrescentar AC-EQP-006-6, AC-EQP-006-7, AC-EQP-006-8 no PRD §US-EQP-006.
- ⚠️ **Antes do go-live público do Aferê** (não MVP-1 dogfooding): textos do aviso E1 + termo de devolução + template de notificação **precisam revisão de advogado humano com OAB ativa** porque serão exibidos a milhares de titulares. Recomendo consulta pontual com advogado LGPD (5+ anos, experiência SaaS B2B operador); preparei este parecer + RAT-EQP-FOTO + textos prontos pra otimizar tempo dele/dela (estimado 2-3h).
- ⏳ Diferido pra V2: blur facial server-side automático (`equipamentos.blur-facial` — depende de infra ML).
- ⏳ Diferido pra Wave B: migração de `termo_devolucao_assinado_url` pra assinatura eletrônica simples Lei 14.063/2020 art. 4º I via portal-cliente.

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º I/II/VI/VII, 6º III/V/VI, 7º II/V, 8º §4º, 11 + §4º, 16 I/II, 18 IV, 37
- Lei 14.063/2020 — art. 4º I (eletrônica simples — aplicável quando portal-cliente entrar, NÃO ao upload presencial atual)
- CPC art. 411 III — documento particular (valor probatório do termo de devolução físico)
- Res. CD/ANPD 15/2024 — incidentes
- Res. CD/ANPD 18/2024 — DPO
- ISO/IEC 17025 cl. 7.4.4 + 7.4.5 — manuseio de item de calibração / condição de chegada
- ISO/IEC 17025 cl. 8.4 — retenção de registros (25 anos quando aplicável)
- INV-005, INV-006, INV-013, INV-EQP-LOC-001, INV-AUTHZ-001, INV-TENANT-001/002 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03, RAT-13, RAT-EQP-FOTO (`docs/conformidade/comum/lgpd-rat.md`)
- DPIA-02 (biometria implícita — análogo conceitual)
- Revisão PRD-advogado §B4 (E1, foto), §D3 (cláusula DPA)
