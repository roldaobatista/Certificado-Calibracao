---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-005
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-005.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-005 (Sucatamento com notificação ao cliente)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. O template do e-mail abaixo será exibido a clientes finais reais antes do go-live público do Aferê e DEVE passar por advogado humano licenciado antes desse momento.

---

## Veredito

**APROVADO COM RESSALVAS.** O plano US-EQP-005 está juridicamente coerente: o gatilho da notificação reflete obrigação ISO 17025 cl. 7.10 (trabalho não-conforme — equipamento sucateado com certificado ainda vigente pode estar em uso por terceiros), o papel do Aferê como operador é preservado (notificação parte em nome do tenant), o audit `equipamento.sucateado_com_certificado_vigente` cita corretamente `cliente_atual_id_hash` (sem nome em claro). As 6 ressalvas abaixo ajustam o template, a UX da foto, o vetor de exercício de direitos do titular e o versionamento do texto.

### Ressalvas (R1–R6)

1. **R1 — Texto do e-mail precisa ser comunicação operacional pura.** A base legal é art. 7º V (execução de contrato comercial tenant↔cliente final), reforçada por dever de boa-fé objetiva (CC art. 422) e diligência ISO 17025 cl. 7.10. NÃO é marketing. Proibido qualquer CTA comercial: "agende nova calibração", "veja nossos planos", "responda esta pesquisa", logo de produto Aferê no rodapé, banner promocional. Cabe APENAS o que está em §3 abaixo. Bundle de comunicação operacional + marketing viola art. 8º §4º LGPD (vedação de empacotar consentimentos/comunicações) e gera reclamação ANPD. O template em constants `notificacao_sucatamento_v1.0-2026-05-18` deve ter comentário no código: `# NÃO ADICIONAR CTA COMERCIAL — base legal art. 7º V exige comunicação estritamente operacional`.

2. **R2 — Versionamento imutável do template é obrigatório.** O nome da constante já carrega versão (`v1.0-2026-05-18`), mas o audit `equipamento.sucateado_com_certificado_vigente` precisa gravar `notificacao_template_versao` no payload, junto de `notificacao_canal` (email | sms | whatsapp — Wave A é apenas evento, mas o campo já fica no schema do audit). Em 2 anos, se cliente alegar "não fui avisado" ou "fui avisado com texto diferente", o tenant precisa provar QUAL texto foi enviado em QUAL data. Sem `notificacao_template_versao` no audit, a prova fica circunstancial. Esse versionamento NÃO afeta o stub `EmptyNotificacaoClienteService` — o evento já carrega o campo agora; o consumer real da Wave B lê dali.

3. **R3 — `cliente_atual_id_hash` está correto, mas reforçar 3 não-campos no payload.** O plano diz "apenas hash". Para evitar regressão silenciosa por agente futuro que "ajude" enriquecendo o payload, o teste `test_payload_audit_cert_vigente_so_hash_de_cliente` deve asserir NEGATIVO contra: (a) `cliente_atual_nome`, (b) `cliente_atual_cpf` / `cliente_atual_cnpj`, (c) `cliente_atual_email`. Audit é WORM e replicado pra B2B/auditores ISO; qualquer PII em claro vira passivo LGPD permanente (não dá pra editar audit retroativamente — só crypto-shredding por chave de tenant). Salt do hash segue o mesmo padrão da correção pós-auditoria CLI-Marco 1 (salt rotativo por tenant + por categoria — `cliente_atual_id_hash` deriva de `tenant_id + hash_salt_cliente + cliente_uuid`).

4. **R4 — UX da foto evidência: aviso ANTES da câmera abrir (espelho E1 da PRD review).** A captura de foto é coleta ativa de dado pessoal potencial (rosto identificável de quem estiver no entorno do equipamento, etiqueta com nome do cliente afixada, ambiente que revele localização do laboratório do tenant). O aviso textual obrigatório, ANTES de a câmera abrir, deve dizer literalmente: *"Esta foto fica como evidência interna do tenant e PODE ser compartilhada com auditores ISO 17025 / IPEM em fiscalização. Não inclua rostos identificáveis nem documentos pessoais visíveis. EXIF (localização do dispositivo) é removido automaticamente."* Sem esse aviso prévio, o operador do tenant pode coletar PII de terceiros (cliente passando atrás) sem base legal — risco LGPD direto pro tenant (art. 7º V não cobre coleta acidental de terceiro). Trigger UX: botão "abrir câmera" só habilita após checkbox "ciente" marcado. Blur facial automático fica V2 (já no plano), mas o aviso prévio é Marco 2 obrigatório, não diferível.

5. **R5 — Direito de contestação do cliente final: o tenant responde, Aferê encaminha em ≤24h.** O cliente final (titular ou não-titular: pode ser PJ contratante sem PF) tem dois vetores possíveis para questionar o sucatamento:
   - **(a) LGPD art. 18** — quando o cliente é PF e quer saber/contestar o tratamento da informação "meu equipamento foi sucateado / por que recebi este e-mail". Resposta: canal do tenant em `/{tenant_slug}/lgpd`. Aferê (operador) encaminha ao tenant em ≤24h (cláusula DPA padrão).
   - **(b) Contestação civil** — quando o cliente alega que o sucatamento foi indevido (equipamento era dele, foi descartado sem autorização, danos morais/materiais). Resposta: relação contratual é tenant↔cliente final; tenant responde. Aferê não é parte. O template do e-mail deve incluir frase de canal de contestação do tenant (placeholder `{tenant_canal_atendimento}`), nunca canal do Aferê. Se o cliente acionar Aferê diretamente, resposta padronizada: "Sua relação contratual é com [tenant]; encaminhamos sua manifestação a eles em até 24h conforme contrato de operação."

6. **R6 — Dispensa de notificação quando cert vigente é do PRÓPRIO tenant (dogfooding).** Cenário-borda real: Balanças Solution (Roldão) sucateia equipamento próprio que tem cert vigente emitido pelo próprio laboratório dela. Não há "cliente externo" a notificar — `cliente_atual_id` aponta pro próprio tenant. O use case deve checar `if cliente_atual_id == tenant_id_proprietario_equipamento: pular notificacao + audit `equipamento.sucateado_com_certificado_vigente_uso_interno`. Sem esse galho, o stub vai gravar evento de notificação que ninguém precisa receber, poluindo audit e — quando o consumer real nascer na Wave B — disparando e-mail do tenant pra ele mesmo (constrangedor + risco de marcar como spam o próprio domínio do tenant).

### Não-ressalvas (validadas como corretas)

- ✅ **Base legal art. 7º V (execução de contrato)** para a notificação: correto. NÃO é consentimento (art. 7º I — esse exige opt-in revogável, inviável para notificação operacional obrigatória ISO 17025). NÃO é obrigação legal direta da LGPD (art. 7º II) — a obrigação vem de ISO 17025 cl. 7.10 e do dever contratual de comunicação de não-conformidade, ambos caem em "execução de contrato comercial e cumprimento de boa-fé objetiva". Não precisa opt-out: cliente não pode "optar por não saber" que equipamento dele virou sucata com cert ainda vigente — a comunicação protege o próprio titular (terceiros poderiam estar usando o cert).
- ✅ **Audit `equipamento.sucateado_com_certificado_vigente` separado de `equipamento.sucateado`:** correto e necessário para auditoria ISO (cl. 7.10 exige rastreabilidade de trabalho não-conforme).
- ✅ **`NotificacaoClienteService` como porta stub Wave A:** correto. O evento já carrega tudo que o consumer real precisa; o atraso na entrega real (até `comunicacao-omnichannel` nascer) NÃO viola LGPD nem ISO porque o evento JÁ ESTÁ no audit imutável — o tenant pode, durante esse intervalo, notificar manualmente via canal próprio puxando do audit. Documentar isso em `CURRENT.md` da Wave A (já está no plano §Riscos #1).
- ✅ **Trigger PG `bloquear_saida_de_sucata` como terminal:** correto. Reversão de sucata sem rastro destrói trilha ISO 17025. Exceção admin Django pra `extraviado` é legítima (cenário: cliente reporta roubo após registro).
- ✅ **Idempotência com TTL 24h:** correto. Sucatamento é destrutivo; reuso de chave em janela longa protege contra double-submit e ataque por replay autenticado.
- ✅ **Rate limit 10 req/min/usuário:** razoável para mutação destrutiva.
- ✅ **EXIF removido server-side:** correto. Geolocalização do dispositivo é dado pessoal de quem tirou a foto + revela localização do laboratório (risco de segurança patrimonial). Remoção server-side (não confiar em client) é a postura correta.

---

## Template do e-mail de notificação — versão `notificacao_sucatamento_v1.0-2026-05-18`

> Esta é a minuta consultiva do template que vai em constants. Comentário no código deve referenciar este parecer.

**Assunto:** Informação importante sobre o equipamento {equipamento_descricao} (Tag {equipamento_tag})

**Corpo (texto plano + HTML simples, sem imagens externas):**

> Prezado(a) {cliente_nome},
>
> Comunicamos, em cumprimento ao item 7.10 da norma ISO/IEC 17025 e às boas práticas de rastreabilidade metrológica, que o equipamento abaixo foi **retirado de uso permanentemente (sucateado)** em nossa base:
>
> - **Equipamento:** {equipamento_descricao}
> - **Identificação (tag):** {equipamento_tag}
> - **Número de série (se aplicável):** {equipamento_numero_serie}
> - **Data do sucatamento:** {data_sucatamento}
>
> **Sobre o certificado de calibração vigente ({certificado_numero}, válido até {certificado_validade}):**
>
> O certificado **permanece válido no histórico** como registro do estado do equipamento na data da calibração, conforme exigência de retenção da ISO/IEC 17025 (cláusula 8.4). **Entretanto, o equipamento NÃO está mais em uso** e, portanto, o certificado **não deve mais ser apresentado como evidência de instrumento operacional** a partir da data acima.
>
> Caso o(a) senhor(a) tenha cópias deste certificado em uso, recomendamos arquivá-las como registro histórico.
>
> **Em caso de dúvida ou contestação sobre esta comunicação**, entre em contato pelo canal oficial: {tenant_canal_atendimento}.
>
> Atenciosamente,
> **{tenant_razao_social}**
> {tenant_cnpj_formatado}
> {tenant_endereco_resumido}

**Rodapé técnico (linha única, fonte menor):**

> Esta é uma comunicação operacional automática enviada em razão da execução do contrato de prestação de serviços de calibração (art. 7º, V, Lei 13.709/2018). Para exercer direitos de titular previstos no art. 18 da LGPD, acesse {tenant_lgpd_link}.

**Placeholders obrigatórios (todos preenchidos pelo consumer real Wave B; stub apenas grava evento):**

- `{cliente_nome}`, `{equipamento_descricao}`, `{equipamento_tag}`, `{equipamento_numero_serie}` (pode ser "não informado")
- `{data_sucatamento}` (formato `DD/MM/AAAA`, fuso `America/Sao_Paulo`)
- `{certificado_numero}`, `{certificado_validade}`
- `{tenant_canal_atendimento}` (e-mail ou telefone de SAC do tenant — placeholder vem do cadastro do tenant)
- `{tenant_razao_social}`, `{tenant_cnpj_formatado}`, `{tenant_endereco_resumido}`
- `{tenant_lgpd_link}` (mesma rota `/{tenant_slug}/lgpd` da R4 do parecer US-CLI-001)

**Justificativa do texto:**

- **Operacional pura** — sem CTA, sem logo Aferê, sem rodapé promocional. Atende R1.
- **Cita expressamente ISO 17025 cl. 7.10 e cl. 8.4** — explica AO cliente por que o cert continua histórico mas o equipamento não está mais em uso (resposta ao questionamento óbvio "então por que vocês mandaram o cert válido?").
- **Cita art. 7º V LGPD no rodapé técnico** — atende princípio da transparência (art. 6º VI) sobre a base legal da comunicação.
- **`{tenant_razao_social}` e `{tenant_canal_atendimento}` em destaque** — reforça quem é o controlador e quem responde por contestação (R5).
- **NÃO menciona Aferê** — Aferê é operador, não emissor da comunicação na percepção do cliente final.
- **Linguagem pt-BR clara, sem jargão jurídico** — cliente final pode ser PF leiga; "trabalho não-conforme" foi traduzido para "retirado de uso permanentemente".

**Variante SMS / WhatsApp (Wave B — registrar agora para evitar improvisação futura):**

> "{tenant_razao_social}: comunicamos que o equipamento {equipamento_tag} foi sucateado em {data_sucatamento}. O certificado {certificado_numero} permanece como registro histórico, mas o equipamento não está mais em uso. Dúvidas: {tenant_canal_atendimento}. Mais informações: {link_versao_completa}."

(Versão completa por SMS/WhatsApp é inviável — link aponta para visualização web do mesmo conteúdo do e-mail; consumer Wave B implementa renderização do link).

---

## Análise por área

### LGPD / Privacidade

- **Papel:** Aferê = operador; tenant = controlador. A comunicação parte EM NOME do tenant — placeholders refletem isso. RAT-03 cobre.
- **Base legal:** art. 7º V (execução de contrato comercial tenant↔cliente final) + dever ISO 17025 cl. 7.10 (que se ancora em "obrigação técnica/contratual aplicável" — art. 7º II como reforço quando o tenant é laboratório acreditado CGCRE). NÃO é consentimento. NÃO é interesse legítimo (art. 7º IX exige LIA — Legitimate Interest Assessment; desnecessário porque a base mais óbvia já cobre).
- **Vedação de bundle (art. 8º §4º):** R1 reforça. Nenhum CTA comercial no template.
- **Direito do titular (art. 18):** rodapé técnico aponta para `{tenant_lgpd_link}`. Aferê encaminha pedido recebido por engano ao tenant em ≤24h (mesma cláusula DPA já firmada).
- **Foto evidência:** aviso prévio R4 + EXIF removed + blur facial V2 mantêm coleta dentro do escopo "execução de contrato" sem extravasar para terceiros acidentalmente capturados.

### Contratual

- DPA tenant↔Aferê deve listar `equipamento.sucateado_com_certificado_vigente` entre os eventos de comunicação operacional automática que o Aferê dispara em nome do tenant — sem renegociação a cada novo tipo de evento. Modelo em `docs/conformidade/comum/dpa-modelo.md` (draft) deve ter anexo "eventos de comunicação automática", item 1: notificação de sucatamento ISO 17025 cl. 7.10.
- Contestação do cliente final (R5b) é relação contratual tenant↔cliente; Aferê não é parte. Se houver pedido judicial nominando Aferê como réu/litisconsorte, escalar IMEDIATAMENTE para advogado humano com OAB ativa.

### Regulatório (ISO 17025 + ANPD + CGCRE)

- **ISO 17025 cl. 7.10 (trabalho não-conforme):** o evento `equipamento.sucateado_com_certificado_vigente` + envio de notificação ao cliente é exatamente o que a cláusula pede. Auditor CGCRE em surveillance pode pedir prova: audit imutável + template versionado servem.
- **ISO 17025 cl. 8.4 (registros):** retenção do certificado em estado "histórico" alinha com retenção matriz (5 anos fiscal + ciclo ISO 17025 ~25 anos). O cert NÃO é deletado pelo sucatamento — apenas o equipamento muda de status.
- **Res. CD/ANPD 15/2024 (incidente):** envio acidental de e-mail com dado errado (placeholder não preenchido, e-mail para destinatário errado, CTA comercial vazado por bug) é incidente potencial; tenant comunica ANPD em ≤3 dias úteis. Aferê comunica tenant em ≤24h (INV-005). Teste de cobertura recomendado: `test_notificacao_falha_se_placeholder_obrigatorio_faltando` (consumer Wave B; registrar como débito Wave A).

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Agente futuro adiciona CTA comercial "agende próxima calibração" no template alegando "engajamento" | Alta sem R1; Baixa com R1 | NC LGPD art. 8º §4º + reclamação ANPD + risco de o cliente marcar tenant como spam | R1 — comentário no código + teste `test_template_nao_contem_palavras_marketing` (whitelist semântica: rejeitar `agende`, `promoção`, `desconto`, `oferta`, `clique aqui`) |
| Payload de audit enriquecido com nome/CPF do cliente "pra facilitar análise" | Média | PII permanente em WORM = passivo LGPD não-removível salvo crypto-shredding | R3 — teste negativo asserindo ausência dos 3 campos PII |
| Foto evidência captura rosto de terceiro que passou no momento | Alta sem R4; Média com R4 | Coleta de PII sem base legal + risco LGPD pro tenant | R4 — aviso prévio + checkbox ciente + EXIF strip; blur facial V2 |
| Cliente final aciona Aferê diretamente por contestação cível, Aferê responde como se fosse parte | Baixa (cliente normalmente vai no tenant) | Reconhecimento implícito de responsabilidade que tenant deveria ter | R5 — resposta padronizada de encaminhamento ao tenant em ≤24h; FAQ interno do suporte Aferê |
| Sucatamento dogfooding Balanças Solution dispara notificação do próprio tenant pra ele mesmo | Alta sem R6; Zero com R6 | Spam pelo próprio domínio + poluição audit | R6 — galho `if cliente_atual_id == tenant_id_proprietario: skip notificacao + audit `_uso_interno` |
| Template `v1.0` vira `v1.1` em 6 meses, audit antigo não consegue reconstruir o texto enviado | Média | Disputa cível: tenant não prova qual texto foi enviado | R2 — `notificacao_template_versao` no payload + texto versionado imutável em `docs/conformidade/comum/templates-notificacao/sucatamento-v1.0.md` (criar) |
| EXIF não removido por bug do adapter, GPS do laboratório vaza | Baixa | Risco patrimonial (endereço operacional) + LGPD do operador | Teste `test_foto_evidencia_exif_removido` (já no plano §T-EQP-056) — manter |

---

## Próximos passos

- ✅ Aplicar R1–R6 no plano `US-EQP-005.md` (autoria: implementador).
- ✅ Criar `docs/conformidade/comum/templates-notificacao/sucatamento-v1.0.md` com o texto §3 versionado imutável (commit-as-source), referenciado pela constant `notificacao_sucatamento_v1.0-2026-05-18`.
- ✅ Adicionar teste `test_template_nao_contem_palavras_marketing` (whitelist semântica) e `test_payload_audit_cert_vigente_so_hash_de_cliente` (asserção negativa para `cliente_atual_nome`, `cliente_atual_cpf`, `cliente_atual_cnpj`, `cliente_atual_email`).
- ✅ Adicionar teste `test_sucatamento_uso_interno_nao_dispara_notificacao` (R6).
- ⚠️ **Antes do go-live público do Aferê** (não MVP-1 dogfooding): texto §3 PRECISA revisão de advogado humano com OAB ativa, conjuntamente com o texto do aceite US-CLI-001. Recomendo consulta pontual com advogado especialista em LGPD + setor regulado (perfil: 5+ anos LGPD, experiência com SaaS B2B operador, familiaridade com ISO 17025/CGCRE preferível); preparei este parecer + RAT-03 + parecer US-CLI-001 para otimizar o tempo dele/dela (estimado 1-2h adicionais para este template).
- ⏳ Diferido para Wave B: implementação do consumer real em `comunicacao-omnichannel` (lê audit, renderiza placeholders, envia via canal configurado pelo tenant).
- ⏳ Diferido para V2: blur facial automático na foto evidência; canal SMS/WhatsApp ativo (template variante já registrado para evitar improvisação).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º VI/VII, 6º III/VI, 7º II/V, 8º §4º, 18, 37, 41
- Código Civil — art. 422 (boa-fé objetiva)
- Res. CD/ANPD 15/2024 — incidentes
- ISO/IEC 17025:2017 — cl. 7.10 (trabalho não-conforme), cl. 8.4 (controle de registros)
- NIT-DICLA-005 e NIT-DICLA-030 (CGCRE — acreditação e rastreabilidade)
- INV-005, INV-006, INV-013, INV-TENANT-001/002 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03 (operador), RAT-06 (opt-in marketing — referência negativa: NÃO é o caso aqui) (`docs/conformidade/comum/lgpd-rat.md`)
- Parecer US-CLI-001-advogado.md (texto do aceite — mesmo rodapé técnico LGPD)
