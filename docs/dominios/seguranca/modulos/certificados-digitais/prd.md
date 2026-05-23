---
owner: roldao
revisado-em: 2026-05-23
status: draft
modulo: certificados-digitais
dominio: seguranca
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0046-ocsp-crl-revogacao-online.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0048-a3-ecpf-rt-cadastro.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
---

# PRD — Certificados Digitais (A1/A3 + e-CPF + e-CNPJ)

## 1. O que é

Gestão centralizada de certificados digitais ICP-Brasil: e-CNPJ da empresa (A1/A3), e-CPF do Responsável Técnico (A3) e e-CPF dos demais signatários autorizados (A3). Registra metadados, vínculos `cpf↔usuario_id↔A3`, status de revogação online (OCSP/CRL) e bloqueia uso de cert revogado/vencido. NÃO armazena chave privada — a chave A3 fica no token físico/HSM do titular (ADR-0009).

## 2. Por que existe

Auditoria Onda 8 detectou que `licencas-acreditacoes` cobria só e-CNPJ (US-LIC-006), sem cadastro do e-CPF do RT (exigido pra assinatura de certificado de calibração — MP 2.200-2/2001 + INV-017) nem dos demais signatários. ADR-0048 cria o cadastro segregado por titularidade; ADR-0046 cobra verificação OCSP em cada assinatura. Sem isso, signatário com cert revogado pela AC continuaria emitindo até alguém perceber manualmente — risco regulatório direto (R-039).

## 3. Personas

- P-SEG-CD-01 — Responsável administrativo (cadastra e-CNPJ + onboarding RT/signatários)
- P-SEG-CD-02 — Responsável Técnico (cadastra próprio e-CPF + revoga ao desligar)
- P-SEG-CD-03 — Signatário não-RT (técnico autorizado a assinar laudos não-RBC)
- P-SEG-CD-04 — Dono Aferê (escalação em revogação detectada)

## 4. Escopo MVP-1 (Wave A)

- 3 cadastros segregados: e-CNPJ empresa, e-CPF RT, e-CPF demais signatários
- Vínculo `cpf ↔ usuario_id ↔ subject_cn` validado no cadastro
- Verificação OCSP em cada assinatura (online, timeout 3s)
- Fallback CRL local (atualizada a cada 1h via job Celery)
- Bloqueio automático ao detectar `revoked` (CertificateStatus revoked/unknown)
- Alertas D-90/60/30/15/7 pré-vencimento
- Audit WORM de cada cadastro/revogação/uso/bloqueio
- Renovação versionada (cada renovação = nova revisão imutável)

## 5. Non-goals MVP-1

- NÃO armazena chave privada nem PFX (chave A3 fica no token; A1 — V2)
- NÃO emite certificados (processo externo na AC ICP-Brasil)
- NÃO substitui o Web PKI Lacuna (ADR-0009 — A3 assina client-side)
- NÃO gerencia tokens físicos (drivers, PIN) — responsabilidade do titular
- NÃO faz timestamping (responsabilidade da TSA — ADR-0047)

## 6. User Stories

### US-CER-DIG-001 — Cadastrar e-CNPJ da empresa

**Persona:** P-SEG-CD-01

- **AC-CER-DIG-001-1 (happy):** GIVEN admin autenticado + arquivo do cert (ou metadados se A3) + CNPJ tenant, WHEN POST `/api/v1/certificados-digitais/e-cnpj`, THEN persiste `{tipo: A1|A3, titular_cnpj, ac_emissora, subject_cn, fingerprint_sha256, valido_de, valido_ate, escopo: empresa}` AND status=`vigente` AND publica evento `CertificadoDigital.Cadastrado{cert_id, escopo:empresa, vence_em}`.
- **AC-CER-DIG-001-2 (CNPJ divergente):** GIVEN cert subject CN.CNPJ ≠ CNPJ do tenant, WHEN POST, THEN 422 `{erro: "CNPJ_DIVERGENTE", esperado, encontrado}`.
- **AC-CER-DIG-001-3 (duplicado):** GIVEN cert já cadastrado (mesmo fingerprint), WHEN POST, THEN 409 `{erro: "JA_CADASTRADO"}`.

### US-CER-DIG-002 — Cadastrar e-CPF do Responsável Técnico (substitui US-LIC-008)

**Persona:** P-SEG-CD-02 (com wizard guiado pelo RT no onboarding)

- **AC-CER-DIG-002-1 (happy):** GIVEN usuário_id ativo com perfil `rt`, WHEN wizard cadastra A3 (informa fingerprint + subject_cn + valido_ate via leitura do token via Web PKI Lacuna), THEN sistema valida `subject_cn.cpf == usuario.cpf` (match exato após normalização) AND executa OCSP online (status=`good`) AND persiste `{escopo: rt_signatario, usuario_id, cpf, ac_emissora, fingerprint, valido_ate}` AND publica `CertificadoDigital.Cadastrado{escopo: rt_signatario}`. **INV-A3-RT-001 satisfeita**.
- **AC-CER-DIG-002-2 (CPF não confere):** GIVEN `subject_cn.cpf != usuario.cpf`, WHEN cadastra, THEN 422 `{erro: "CPF_DIVERGENTE", cpf_usuario_hash, cpf_cert_hash}` + audit `A3.CadastroRejeitadoMatchCPF`.
- **AC-CER-DIG-002-3 (OCSP revoked):** GIVEN OCSP retorna `revoked`, WHEN cadastra, THEN 422 `{erro: "CERT_REVOGADO_NA_AC"}` + audit `A3.RevogacaoDetectadaCadastro`.
- **AC-CER-DIG-002-4 (RT inativo):** GIVEN usuário sem perfil `rt` ativo, WHEN cadastra A3 com escopo `rt_signatario`, THEN 403 (INV-AUTHZ-001).

### US-CER-DIG-003 — Cadastrar e-CPF de signatário não-RT (US-LIC-009 reposicionada)

- **AC-CER-DIG-003-1:** GIVEN usuário com perfil `signatario_autorizado`, WHEN cadastra A3 próprio (mesma validação CPF↔subject_cn + OCSP), THEN persiste com `escopo: signatario` AND publica evento.
- **AC-CER-DIG-003-2 (escopo limitado):** GIVEN signatário não-RT, WHEN tenta usar cert pra assinar certificado RBC (calibração), THEN módulo `certificados` bloqueia hard 403 — apenas RT assina RBC.

### US-CER-DIG-004 — Verificação OCSP/CRL online em cada assinatura

**Trigger:** chamada do módulo `certificados` ao assinar PDF (US-CER-002) ou módulo `fiscal` ao emitir NF (US-FIS-001).

- **AC-CER-DIG-004-1 (happy OCSP):** GIVEN cert vigente + signatário tenta assinar, WHEN porta `CertificadoDigital.verificar_status(cert_id)` é invocada, THEN consulta OCSP online (timeout 3s), retorna `{status: good, verificado_em, fonte: ocsp}`, assinatura prossegue. Audit `A3.VerificacaoOCSPSucesso`.
- **AC-CER-DIG-004-2 (OCSP revoked):** GIVEN AC revogou cert, WHEN consulta, THEN retorna `{status: revoked, motivo, revogado_em}`, módulo cliente bloqueia operação com 409 `{erro: "CERT_REVOGADO"}`, publica `A3.RevogacaoDetectada{cert_id, fonte: ocsp}`, marca `status_local=revogado`, alerta escalação P1 ao dono Aferê. **INV-A3-OCSP-001 satisfeita**.
- **AC-CER-DIG-004-3 (fallback CRL):** GIVEN OCSP timeout > 3s, WHEN consulta CRL local (job atualizou < 1h atrás), THEN se cert na CRL → bloqueia; se não → permite com flag `verificacao_degraded=true` em audit.
- **AC-CER-DIG-004-4 (CRL stale):** GIVEN CRL local > 1h sem atualização + OCSP indisponível, WHEN tenta assinar cert RBC, THEN bloqueia 503 `{erro: "VERIFICACAO_INDISPONIVEL"}` (cert RBC exige verificação atual); cert não-RBC permite com flag.

### US-CER-DIG-005 — Alertas de vencimento

- **AC-CER-DIG-005-1:** GIVEN cert com `valido_ate` em D-90/60/30/15/7, WHEN job diário roda, THEN dispara notificação ao titular + admin tenant via WhatsApp+email (respeita opt-out cliente per INV-CLI-OPT-001 quando aplicável — neste módulo só notifica colaboradores internos).

### US-CER-DIG-006 — Revogar e-CPF ao desligar RT/signatário

**Trigger:** evento `Colaborador.Desligado` (INV-INT-011).

- **AC-CER-DIG-006-1:** GIVEN evento recebido + colaborador tem A3 cadastrado, WHEN consumer reage em ≤2s, THEN marca cert local como `status=revogado_localmente`, motivo=`desligamento`, publica `CertificadoDigital.RevogadoLocalmente`. Não chama AC (titular precisa revogar formalmente — sistema lembra ele).

## 7. NFR

- Verificação OCSP p95 < 2s; p99 < 3s (timeout duro 3s)
- Job atualização CRL: diário 02:00 BRT + on-demand a cada 1h por cert
- Disponibilidade: 99.9% (módulo crítico — bloqueia emissão)
- Audit WORM de toda verificação (rastreabilidade Cgcre + LGPD)

## 8. Invariantes

- **INV-A3-RT-001** — RT signatário só assina com e-CPF próprio vinculado ao `usuario_id` ativo (validado em cadastro + cada uso)
- **INV-A3-OCSP-001** — Cert revogado pela AC bloqueia assinatura com 409 + audit `A3.RevogacaoDetectada`
- **INV-CER-LTV-001** — Cert calibração exige carimbo PAdES-LTV (ADR-0047 — verificado no módulo `certificados`, declarado aqui)
- INV-017 (ICP-Brasil A3/A1 obrigatório), INV-001 (audit), INV-013 (acesso restrito)

## 9. Dependências

- ADR-0009 (A3 assina client-side via Web PKI Lacuna)
- ADR-0046 (OCSP/CRL — esta porta de verificação)
- ADR-0047 (TSA-ITI carimbo PAdES-LTV)
- ADR-0048 (cadastro 3 titularidades)
- `licencas-acreditacoes` (US-LIC-006 do e-CNPJ migra dependência: cadastro físico fica aqui, controle de vencimento/bloqueio operacional permanece lá via referência cruzada)
- `acesso-seguranca` (evento `Colaborador.Desligado`)
- `metrologia/certificados` (consumidor — US-CER-002 assinar)
- `fiscal` (consumidor — US-FIS-001 emitir NF)

## 10. Eventos publicados

- `CertificadoDigital.Cadastrado{cert_id, escopo, titular_id, vence_em}`
- `CertificadoDigital.Renovado{cert_id, versao_anterior_id}`
- `CertificadoDigital.RevogadoLocalmente{cert_id, motivo}`
- `A3.RevogacaoDetectada{cert_id, fonte: ocsp|crl, detectado_em}` — escalação P1
- `A3.VerificacaoOCSPSucesso{cert_id, verificado_em}` (amostrado em audit)
- `A3.CadastroRejeitadoMatchCPF{usuario_id, motivo}`
