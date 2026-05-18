---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# PRD — Módulo Equipamentos do cliente

> **Histórico:**
> - **v1 (draft 2026-05-17):** primeira passagem do PRD com 3 US (cadastrar+QR, editar+versionar, ficha 360°+scan).
> - **v2 (stable 2026-05-18):** revisão pelos 4 subagentes (`tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`) endereçou 16 bloqueadores. Pareceres em `revisoes/PRD-*.md`. Escopo expandiu para 6 US cobrindo ISO 17025 cl. 7.4 completo (decisão Roldão).

## 1. O que este módulo é

Cadastro completo do equipamento físico do cliente final (balança, paquímetro, termômetro etc.) que o tenant calibra. Cada equipamento tem TAG única por tenant (INV-049), QR Code impresso com hash assinado (INV-051), vínculo a um cliente e histórico imutável de eventos após primeira emissão de certificado (INV-025). Persona principal: metrologista de bancada (P-OP-02), técnico de campo (P-OP-01) e almoxarife (P-OP-03). **Wave A · Marco 2** — destrava OP2 (rastreio de calibração), OP3 (notificação de vencimento) e o fluxo ISO 17025 cl. 7.4 (recebimento e devolução do item).

## 2. Por que existe (problema a resolver)

- BIG-01 (não perder info do equipamento entre OS sucessivas)
- OP17 (ficha 360° + QR Code escaneável)
- Conformidade ISO 17025 cl. 7.4 (manuseio do item) + cl. 7.8 (identificação inequívoca) + cl. 8.4 (registros imutáveis)
- Dor: cliente liga e técnico não acha histórico do instrumento.
- Dor: lab recebe equipamento avariado e não tem evidência da condição de chegada (cliente alega "veio quebrado pelo lab").

## 3. Personas

- **P-OP-02 — Metrologista de bancada** (principal): cadastra, edita, recebe, calibra, sucata, aprova versões pós-cert.
- **P-OP-01 — Técnico de campo**: escaneia QR, consulta ficha mobile.
- **P-OP-03 — Almoxarife** (novo — promovido após auditoria PRD 2026-05-18): recebe equipamento na portaria do lab, imprime etiqueta com TAG provisória, registra condição visual de chegada (foto + checklist).
- **P-COM-01 — Atendente/recepção**: cadastro inicial, transferência entre clientes do mesmo tenant.

Detalhes em `personas.md`.

## 4. Escopo (o que ESTÁ)

- CRUD de equipamento (TAG única por tenant, NS, fabricante, modelo, faixa, classe, vínculo a cliente)
- Geração e impressão de QR Code com hash HMAC-SHA256 + KMS_qr_secret (INV-051)
- Ficha 360°: dados + histórico de calibração + OS abertas + próxima calibração + eventos (via portas stub para módulos certificados e OS que ainda não existem)
- Versionamento de atributos descritivos pós-emissão de certificado (INV-025) com motivo de mudança enum controlado
- Transferência de equipamento entre clientes **do mesmo tenant** (INV-050) com aceite duplo (cedente + cessionário)
- Sucatamento com notificação automática ao cliente se há certificado vigente
- Status / máquina de estados expandida: ativo / inativo_temporario / aposentado / em_calibracao_lab (sub-fluxo) / sucata / orfao_pendente_decisao / extraviado
- **Recebimento físico no laboratório** (ISO 17025 cl. 7.4): entidade `EquipamentoRecebimento` com condição visual + foto obrigatória em perfil A, checklist de anomalias, decisão antes de prosseguir

## 5. Non-goals

- NÃO emite certificado (fica em Metrologia / módulo `certificados`)
- NÃO calcula incerteza de medição
- NÃO controla estoque do tenant (o equipamento é do cliente final, não do tenant)
- NÃO faz cobrança (vai pra Financeiro)
- **NÃO transfere equipamento entre tenants diferentes** (INV-050 — proibido)
- NÃO trata padrão metrológico do laboratório (esse fica em módulo `padroes` separado — INV-021/022/023)
- NÃO entrega blur facial automático em fotos no Marco 2 (V2 quando infra ML estiver pronta — fluxo manual via aviso UX no Marco 2)
- NÃO entrega app Flutter no Marco 2 (Tela 5 vira PWA — ADR-0018)
- NÃO entrega sincronização offline-first (ADR-0004, Wave B)

## 6. User Stories

### US-EQP-001: Cadastrar equipamento com QR Code

**Como** almoxarife/atendente, **quero** cadastrar um equipamento e imprimir QR Code, **para** identificar fisicamente o ativo.

- **AC-EQP-001-1**: GIVEN tenho cliente cadastrado, WHEN preencho TAG (única por tenant) + NS + fabricante + modelo + faixa + classe, THEN equipamento é salvo, QR Code é gerado com hash HMAC-SHA256 + KMS_qr_secret, e snapshot `perfil_tenant_no_momento_cadastro` é congelado.
- **AC-EQP-001-2**: GIVEN equipamento salvo, WHEN clico "imprimir etiqueta", THEN PDF da etiqueta sai com QR + TAG + NS + logo tenant.
- **AC-EQP-001-3**: GIVEN tento cadastrar com TAG já existente no mesmo tenant, THEN sistema retorna 409 com mensagem "TAG já existe — escolha outra".
- **AC-EQP-001-4**: GIVEN preencho `localizacao_fisica` com texto contendo CPF/nome próprio/e-mail, THEN sistema retorna 400 (INV-EQP-LOC-001) com texto orientando a remover.

**Invariantes:** `INV-049` (TAG única), `INV-051` (QR HMAC), `INV-EQP-LOC-001` (localização anti-PII), `INV-TENANT-001`.

### US-EQP-002: Editar equipamento com versionamento pós-emissão

**Como** metrologista, **quero** editar atributo descritivo de equipamento já com certificado emitido, **para** corrigir info sem violar imutabilidade do certificado.

- **AC-EQP-002-1**: GIVEN equipamento com ≥1 certificado emitido, WHEN edito atributo versionável (modelo, faixa, classe, descrição, localização), THEN sistema cria nova `EquipamentoVersao` com `motivo_mudanca` (enum controlado) + snapshot dos novos valores + `cliente_atual_id_no_momento`. Certificados antigos continuam referenciando a versão original.
- **AC-EQP-002-2**: GIVEN tento alterar TAG, NS ou fabricante de equipamento com certificado, THEN sistema bloqueia (campos imutáveis pós-cert — INV-025).
- **AC-EQP-002-3**: GIVEN tenant em perfil A E edito `classe_exatidao` ou `faixa_medicao`, THEN sistema exige assinatura A3 do RT antes de gravar; assinatura registrada em audit WORM.
- **AC-EQP-002-4**: GIVEN escolho motivo_mudanca = "outros", THEN sistema exige justificativa ≥100 chars + aprovação do gestor de qualidade.

**Invariantes:** `INV-025`, `INV-EQP-LOC-001`.

### US-EQP-003: Escanear QR Code e abrir ficha 360°

**Como** técnico de campo / metrologista / cliente final, **quero** escanear QR Code, **para** ver dados do equipamento no celular ou desktop.

- **AC-EQP-003-1**: GIVEN QR válido + sessão autenticada do **mesmo tenant**, WHEN escaneio, THEN ficha 360° completa abre em ≤ 1.5s (p95) — dados cadastrais + versões + certificados (via porta stub) + OS abertas (via porta stub) + eventos.
- **AC-EQP-003-2**: GIVEN QR válido + sessão de **outro tenant**, WHEN escaneio, THEN sistema retorna payload mínimo (Escopo B — sem PII, sem histórico) com mensagem "ativo de outro tenant — confidencial".
- **AC-EQP-003-3**: GIVEN QR válido + **sem sessão** (anônimo), WHEN escaneio, THEN sistema retorna payload mínimo (Escopo C — sem PII, sem identificação do tenant) com mensagem genérica "contate o operador".
- **AC-EQP-003-4**: GIVEN QR revogado/inválido, THEN sistema retorna 404 indistinguível de "hash de outro tenant" (sem oracle de enumeração).
- **AC-EQP-003-5**: GIVEN 100+ tentativas 4xx do mesmo IP em 1h, THEN IP bloqueado por 24h + alerta P2.
- **AC-EQP-003-6**: Tela 5 (Scanner QR mobile) funciona em PWA com `BarcodeDetector API` nativo + fallback jsQR — ADR-0018.

**Invariantes:** `INV-051`, `INV-AUTHZ-001`, `INV-TENANT-001`.

### US-EQP-004: Transferir equipamento entre clientes do mesmo tenant

**Como** atendente/metrologista, **quero** transferir vínculo de equipamento de um cliente para outro do mesmo tenant, **para** registrar mudança de titularidade (venda, comodato, doação, correção cadastral).

- **AC-EQP-004-1**: GIVEN equipamento existente + novo cliente do mesmo tenant + aceite cedente + aceite cessionário, WHEN executo transferência com `motivo_categoria` (enum: venda/comodato/doacao/correcao_cadastral/outro), THEN `cliente_atual_id` atualiza, `cliente_id_original` permanece imutável, evento `equipamento.transferido` publica em audit com payload sanitizado.
- **AC-EQP-004-2**: GIVEN tento transferir para cliente_id de outro tenant (ataque cross-tenant), THEN sistema retorna 422 com mensagem genérica "cliente não encontrado neste tenant" — INV-050.
- **AC-EQP-004-3**: GIVEN cliente cedente está bloqueado OU tem fatura aberta referente ao equipamento, THEN transferência é bloqueada com mensagem "regularize antes de transferir".
- **AC-EQP-004-4**: GIVEN transferência concluída, WHEN cessionário acessa ficha 360°, THEN histórico de certificados anteriores fica **oculto** (cl. 4.2 ISO 17025 — confidencialidade) com mensagem "histórico anterior preservado mas confidencial — solicite ao vendedor".

**Invariantes:** `INV-050`, `INV-025`, `INV-TENANT-001`.

### US-EQP-005: Sucatar equipamento com notificação

**Como** metrologista, **quero** marcar equipamento como sucata, **para** registrar fim da vida útil + notificar cliente se há certificado vigente.

- **AC-EQP-005-1**: GIVEN equipamento sem OS aberta + sem cert vigente, WHEN sucateio com motivo + foto opcional, THEN status → `sucata`, evento `equipamento.sucateado` publica.
- **AC-EQP-005-2**: GIVEN equipamento tem `Certificado.status=emitido AND data_proxima_calibracao > now()`, WHEN sucateio, THEN sistema exige confirmação dupla + dispara evento `equipamento.sucateado_com_certificado_vigente` → consumer `comunicacao-omnichannel` envia e-mail ao cliente final ("seu equipamento foi sucateado; certificado X permanece como registro histórico mas equipamento não está mais em uso").
- **AC-EQP-005-3**: Sucata é estado terminal — não reativa (admin pode mudar pra `extraviado` se cliente reportar perda/roubo).

**Invariantes:** `INV-025`, `INV-INT-002` (transição regulatória análoga).

### US-EQP-006: Receber equipamento no laboratório (ISO 17025 cl. 7.4)

**Como** almoxarife, **quero** registrar entrada física do equipamento no laboratório com condição visual e foto, **para** atender ISO 17025 cl. 7.4 e proteger o lab de reclamações "veio quebrado".

- **AC-EQP-006-1**: GIVEN equipamento já cadastrado (ou cadastro provisório), WHEN registro entrada física com `condicao_visual_chegada` (enum: integro/amassado/lacre_violado/contaminado/outros) + ≥1 foto (obrigatória em perfil A; opcional B/C/D) + lacre + recebedor + data/hora, THEN `EquipamentoRecebimento` criado, status_fluxo_lab inicia em `recebido_pendente_inspecao`, EXIF removido das fotos.
- **AC-EQP-006-2**: GIVEN condição != integro, WHEN registro entrada, THEN sistema exige `decisao_apos_anomalia` (enum: prosseguir/contatar_cliente_aguardando/recusar_devolver/prosseguir_com_ressalva) + justificativa ≥30 chars; cliente é notificado se decisão = `contatar_cliente_aguardando`.
- **AC-EQP-006-3**: Máquina de estados `status_fluxo_lab` percorre: `aguardando_recebimento → recebido_pendente_inspecao → em_inspecao_visual → aguardando_calibracao → em_calibracao → aguardando_aprovacao_tecnica → aguardando_devolucao → devolvido`. Caminhos alternativos: `nao_conformidade_recebimento`, `nao_conformidade_calibracao`.
- **AC-EQP-006-4**: GIVEN devolução ao cliente, WHEN registro saída física, THEN `EquipamentoRecebimento.data_hora_devolucao` + `condicao_visual_devolucao` + `fotos_devolucao` + `termo_devolucao_assinado_url` (assinatura cliente via portal ou presencial).
- **AC-EQP-006-5**: Foto de chegada/devolução: EXIF removido no upload + aviso UX antes da câmera (E1 da revisão advogado) + limite ≤5MB + scan automático bloqueando se OCR detectar CPF/CNPJ em texto na foto (V2 — Marco 2 deixa em aviso textual).

**Invariantes:** `INV-025`, `INV-AUTHZ-001`, ISO 17025 cl. 7.4.4 + 7.4.5.

## 7. Bases legais LGPD (art. 7º)

| Finalidade | Base legal | Justificativa |
|---|---|---|
| Cadastro de equipamento (CRUD) | art. 7º V | Execução de contrato; cadastro é meio operacional |
| Versionar atributo pós-cert (INV-025) | art. 7º II + art. 16 I | Obrigação regulatória (ISO 17025 cl. 7.8 + 8.4) prevalece sobre direito ao esquecimento |
| Imprimir QR Code físico | art. 7º V | Identificação operacional |
| Ficha 360° via scan (mesmo tenant) | art. 7º V + art. 7º VI | Necessidade operacional + INV-013 |
| Scan anônimo / outro tenant | art. 7º III | Interesse legítimo — só mensagem genérica sem PII |
| Transferir entre clientes finais | art. 7º V + art. 7º VI | Aferê é operador; aceite duplo é obrigação contratual (CC 421/422), não LGPD |
| Sucatear equipamento | art. 7º V | Operacional; histórico sob art. 7º II (ISO 17025) |
| Notificação sucata + cert vigente | art. 7º V + art. 7º II | Comunicação operacional, não marketing |
| Foto do equipamento (RAT-EQP-FOTO) | art. 7º V (técnica) ou art. 11 § 4º (sensível se rosto) | Registro técnico; rosto identificável vira sensível com base no controlador (tenant) |
| Audit trail (eventos imutáveis) | art. 7º II + art. 16 I + Marco Civil art. 15 | Imutabilidade exigida; payload sanitizado (hashes) |
| Histórico com `cliente_id_original_hash` pós-shredding | art. 7º II + art. 16 I | Hash satisfaz ISO 17025; não é PII reidentificável (salt por tenant) |
| Recebimento físico no lab (foto + condição) | art. 7º V + ISO 17025 cl. 7.4.4 | Registro técnico obrigatório em perfil A |

## 8. Métricas (ver `metricas.md`)

- Tempo médio para localizar equipamento ≤ 30s
- % equipamentos com QR impresso ≥ 90%
- Taxa de scan QR / mês
- % recebimentos com foto + condição visual em perfil A: 100%

## 9. NFR

- Performance: ficha 360° p95 ≤ 1.5s (índice composto `(tenant_id, equipamento_id, created_at DESC)` em eventos e versões; cache só se medido falhar)
- Segurança: leitura do QR exige `AuthorizationProvider.can()` em todos modos; rate limit por IP + lockout
- Acessibilidade: WCAG AA
- Compatibilidade scanner: Chrome Android (BarcodeDetector nativo), iOS Safari 17+ (BarcodeDetector nativo), iOS 16 (jsQR fallback), Firefox/outros (jsQR fallback)

## 10. ADRs e INVs aplicáveis

- ADR-0002 (multi-tenancy RLS), ADR-0007 (camada domínio + codegen), ADR-0010 (HTMX + 4 SPAs), ADR-0012 (AuthorizationProvider), ADR-0014 (transições regulatórias), ADR-0018 (PWA scanner QR — proposta), ADR-0019 (responsabilidade agente IA — proposta)
- INV-025 (imutabilidade pós-cert), INV-049 (TAG única), INV-050 (transferência intra-tenant), INV-051 (QR HMAC + allowlist público), INV-EQP-LOC-001 (localização anti-PII), INV-TENANT-001..004, INV-AUTHZ-001..003

## 11. Glossário e referências

- `glossario.md` — termos específicos do módulo
- `modelo-de-dominio.md` — entidades, agregados, portas, eventos
- `personas.md` — personas operacionais
- `metricas.md` — KPIs + SLI/SLO
- `contratos/{api,ui,exports}.md` — interfaces externas
- `revisoes/PRD-{tech-lead,advogado,corretora,rbc}.md` — pareceres dos 4 subagentes (2026-05-18)
- `docs/conformidade/equipamentos/qr-publico-allowlist.md` — política de exposição QR público
- `docs/conformidade/comum/lgpd-rat.md` — RAT-EQP-FOTO
- `docs/conformidade/comum/retencao-matriz.md` — 5 linhas equipamento
