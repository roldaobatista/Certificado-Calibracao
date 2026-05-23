---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# DPIA — Módulo OS (Marco 3)

> Plataforma Aferê — LGPD art. 38 + Res. CD/ANPD 18/2024.
> **MINUTA — REQUER VALIDAÇÃO OAB**.

---

## 1. Descrição da Operação

1.1. **Módulo:** Ordens de Serviço (OS) com Atividades (ADR-0023 — 1 OS contém N AtividadeDaOS).
1.2. **Marco:** Marco 3 (pré-Marco 4 calibração).
1.3. **Operações principais:**
- abertura de OS pelo atendente do Tenant (vinculada a Cliente Final + Equipamento);
- criação de Atividades por tipo (calibração, manutenção corretiva/preventiva, instalação, verificação INMETRO, vistoria);
- check-in/check-out do técnico em campo (com geolocalização opt-in — RAT-07);
- captura de foto de evidência da atividade;
- aceite touch (biometria) do cliente final no encerramento — INV-OS-ACEITE-BIO-001;
- transição de estado da Atividade (CONCLUIDA / NAO_CONFORME / CANCELADA);
- agregação automática do estado da OS a partir das Atividades — INV-OS-ATIV-001;
- sincronização offline-first (ADR-0027) com merge por atividade_id.

---

## 2. Finalidade

- `obrigacao_regulatoria_iso17025` (para atividades de calibração que alimentam Marco 4)
- `tecnico_campo` (execução de contrato — art. 7º V)
- `comunicacao_servico_titular` (notificações ao Cliente Final)
- `defesa_em_juizo` (prova da prestação dos serviços)
- `auditoria_cgcre` (quando OS contém atividade de calibração que origina certificado RBC)

---

## 3. Necessidade e Proporcionalidade

3.1. **Necessidade:**
- identificação do técnico executor é exigência de cl. 6.2 ISO 17025 quando a OS contém calibração;
- registro de localização/horário é necessário para defesa do Tenant em ações trabalhistas + cobranças contestadas;
- aceite biométrico (touch) é necessário para constituir prova vinculante do serviço prestado (Lei 14.063/2020 art. 4º).

3.2. **Proporcionalidade:**
- geolocalização **somente** em check-in/check-out, **nunca** tracking contínuo;
- precisão da geo no payload de evento limitada a município/bairro — INV-OS-GEO-001;
- biometria touch validada (≥8 pontos + bounding box ≥30×20px — anti-rabisco vazio);
- alternativa de assinatura desenhada disponível ao Cliente Final;
- captura de foto restrita ao instrumento — orientação ao técnico para evitar enquadramento de pessoas/documentos.

---

## 4. Titulares e Dados

| Titular | Dados |
|---|---|
| Cliente Final (PJ ou PF) | Razão social/nome, endereço, contato, equipamento sob serviço |
| Cliente Final (PF representante) | Nome, CPF parcial (4 últimos dígitos para conferência), assinatura touch |
| Técnico executor (colaborador do Tenant) | Nome, CPF, geolocalização durante atividade (opt-in), foto perfil |
| RT do Tenant (quando atividade exige) | Nome, CPF, registro conselho |
| Atendente do Tenant (abertura da OS) | Nome, CPF |

---

## 5. Bases Legais

| Dado | Base LGPD | Justificativa |
|---|---|---|
| Cliente Final identificação | art. 7º V + VI | Execução contrato + defesa |
| Geolocalização técnico | art. 7º I + IX | Consentimento opt-in + legítimo interesse (operacional/auditoria) |
| Assinatura biométrica touch | art. 11 II "g" + "a" | Lei 14.063/2020 + consentimento específico |
| Foto de instrumento | art. 7º V | Execução contrato + comprovação técnica |
| Técnico, atendente, RT | art. 7º V + II + 11 II "a" | Contrato + obrigação regulatória |
| Audit log universal | art. 7º II | Obrigação legal — ISO 17025 cl. 8.4 + Marco Civil art. 15 |

---

## 6. Retenção

6.1. **5 anos** para OS sem vínculo regulatório (Receita + defesa civil).
6.2. **~25 anos** para OS que contém atividade de calibração emitindo certificado (vínculo cl. 8.4 ISO 17025).
6.3. **Biometria touch:** 5 anos quando OS não-calibração; preservada por 25 anos quando vinculada a certificado.
6.4. **Geolocalização exata:** retenção máxima 5 anos com truncamento para município após o prazo (INV-OS-GEO-001 + RIPD).
6.5. **Pedido de eliminação:** segue ADR-0021 — Zona A (foto sem vínculo regulatório), Zona C (foto/geo vinculada a calibração ISO).

---

## 7. Garantias de Segurança

- RLS multi-tenant (INV-TENANT-003) + middleware tenant_id;
- audit imutável WORM (`EventoDeOS`) com payload sanitizado — INV-OS-AUD-001;
- biometria cifrada com chave KMS dedicada `BIOMETRIA_KEY_<tenant>` separada da chave geral PII — INV-OS-ACEITE-BIO-001;
- canonicalização determinística do texto do aceite (ADR-0029) para hash probatório;
- sincronização offline com merge por atividade_id (ADR-0027) — LWW + IDEMP-001 + backlog visível;
- cache offline cifrado com chave derivada de PIN/biometria do device;
- nonce + signing-time server-controlled (defesa anti-replay);
- IP hash HMAC (anti-PII em logs);
- captura de geo opt-in com consentimento explícito.

---

## 8. Anonimização (ADR-0021)

8.1. **Zona aplicável por dado:**
- Foto de evidência sem vínculo regulatório → **Zona A** (eliminação efetiva possível);
- Foto vinculada a calibração ISO → **Zona C** (anonimização em lugar — preserva metadados técnicos);
- Geolocalização granular após 5 anos → truncamento município (Zona C);
- Biometria touch após 5 anos (OS não-calibração) → purge do hash + metadados, descarte do traçado;
- Texto livre em razão_cancelamento → hash com salt por tenant após 5 anos (Zona C);
- Identificação Cliente Final → Zona conforme matriz `retencao-matriz.md`.

8.2. **Pedido de eliminação titular técnico desligado:** hash biometria + 30 dias → purge; demais dados retidos por base legal autônoma (defesa, fiscal, ISO).

---

## 9. Riscos Identificados

| # | Risco | Probabilidade | Impacto | Severidade |
|---|---|---|---|---|
| R1 | Vazamento de foto site cliente (revelar layout, equipamento sensível, sigilo industrial) | Baixa | Alto | Médio |
| R2 | Geolocalização técnico expor padrão de deslocamento → risco pessoal | Baixa | Alto | Médio |
| R3 | Biometria touch comprometida (extração de hash + rainbow) | Muito baixa | Alto | Médio |
| R4 | QR de equipamento forjado → OS executada em ativo errado | Baixa | Médio | Baixo |
| R5 | Sincronização offline com merge errado expondo dado cross-tenant | Muito baixa | Crítico | Médio |
| R6 | Foto de aceite com dado sensível incidental (documento aberto na mesa) | Média | Médio | Médio |
| R7 | Cache offline em dispositivo perdido/roubado | Baixa | Alto | Médio |
| R8 | Replay de assinatura A3 (mesmo nonce reutilizado) | Muito baixa | Crítico | Médio |

---

## 10. Medidas de Mitigação

- **R1:** orientação de captura mínima; blur automático de rostos (roadmap); marcação de tenant "sigilo industrial" cifra foto com chave do Cliente Final; treinamento do técnico.
- **R2:** geo **somente** em check-in/check-out; aviso explícito no primeiro uso do app; retenção 5 anos + truncamento município (INV-OS-GEO-001).
- **R3:** hash com salt por tenant + chave KMS `BIOMETRIA_KEY_<tenant>` dedicada; rotação anual; nunca exportação do hash; watermark vinculado a `tenant_id|atividade_id|aceito_em_iso`.
- **R4:** ADR-0029 canonicalização determinística do hash; QR validado server-side com HMAC (INV-051); hook `qr-hmac-check`.
- **R5:** merge por atividade_id (ADR-0027) com LWW + IDEMP-001; RLS no servidor bloqueia cross-tenant; testes regressão.
- **R6:** aviso ao técnico antes de capturar; revisão pré-upload; treinamento.
- **R7:** cache cifrado com chave derivada do PIN/biometria do device; wipe remoto via MDM/sessão revogada; tempo máximo de cache configurável.
- **R8:** nonce + signing-time server-controlled + one-shot (ADR-0009); rejeição de signing_time fora de ±5min do servidor.

---

## 11. Consulta a Titulares

11.1. Não exigida diretamente (B2B regulado); canal DPO público.
11.2. Tenant piloto (Balanças Solution) consultado durante dogfooding.
11.3. **Recomendação para Wave A externa:** consulta direta a amostra de 3 a 5 técnicos de campo e 3 a 5 Clientes Finais antes do go-live em tenant externo pago. Roteiro a elaborar pelo DPO.

---

## 12. Conclusão

12.1. **Veredito:** operação proporcional à finalidade; **risco residual MÉDIO** após mitigações, com pontos de atenção ALTOS pendentes de execução (R1 blur foto, R3 fluxo biometria, R6 cache cifrado, R7 wipe remoto).

12.2. **Pendências bloqueantes pré-Marco 3 produção:**
- aceite formal ADR-0023 (já aceita), ADR-0027 (em proposta), ADR-0029 (já aceita);
- hook `qr-hmac-check` ativo (já existe — Marco 2);
- hook `biometria-key-validator.sh` ativo (criado Onda 4 saneamento — 2026-05-23);
- hook `os-conclusao-todas-terminais-check.sh` ativo (criado Onda 4);
- hook `termo-canonicalizacao-check.sh` (pendente — Marco 3 P4);
- validação OAB deste DPIA.

12.3. **Reavaliação:** após cada mudança material no fluxo OS; após incidente; anualmente; em mudança regulatória.

---

## 13. Aprovações

| Papel | Responsável | Data | Status |
|---|---|---|---|
| Elaboração técnica | subagente `advogado-saas-regulado` (IA) | 2026-05-23 | minuta |
| DPO (Encarregado PF) | [a designar] | — | pendente |
| Revisão jurídica | advogado(a) com OAB ativa | — | pendente |
| Ciência da diretoria | Roldão (founder) | — | pendente |

---

**FIM DPIA-OS v1.0 — MINUTA — REQUER VALIDAÇÃO OAB**
