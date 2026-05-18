---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Personas — Módulo Equipamentos do cliente

> Específicas deste módulo. Transversais em `../../personas.md` e `docs/comum/personas.md`.
> **v2 (2026-05-18):** P-OP-03 (Almoxarife) promovido após auditoria PRD — gap detectado por tech-lead C6 (almoxarife em api.md sem entrada em personas.md).

---

## Persona principal: Metrologista de bancada (P-OP-02)

Detalhes em `docs/dominios/operacao/personas.md`. Toca este módulo ao:
- Cadastrar equipamento novo recém-chegado pra calibrar.
- Editar atributo descritivo (gera nova versão se já há certificado — INV-025).
- Conferir ficha 360° antes de iniciar calibração.
- Aprovar versionamento com motivo de mudança (enum controlado — em perfil A assina com A3 se altera classe/faixa).
- Sucatar equipamento (com confirmação dupla se há cert vigente — US-EQP-005).
- Avançar status_fluxo_lab dentro da máquina de estados de recebimento (US-EQP-006).

**Frequência:** diária.
**Device:** web desktop principal; mobile para leitura QR.

---

## Persona secundária: Técnico de campo (P-OP-01)

Toca este módulo ao:
- Escanear QR no cliente para abrir ficha 360° (PWA — ADR-0018).
- Confirmar TAG e NS antes de iniciar trabalho em campo.
- Consultar histórico de calibração para identificar próxima necessidade.

**Frequência:** diária.
**Device:** mobile (PWA Marco 2; app Flutter Wave B — ADR-0003).

---

## Persona promovida: Almoxarife do laboratório (P-OP-03)

> **Novo na v2 (2026-05-18).** Promovido pela auditoria do PRD — gap apontado pelo subagente `tech-lead-saas-regulado` (C6) e reforçado pelo `consultor-rbc-iso17025` (B1/B2 — ISO 17025 cl. 7.4).

**Quem é:** funcionário do tenant responsável pelo recebimento físico do equipamento na portaria/almoxarifado do laboratório, antes de o instrumento ir pra bancada do metrologista.

**Toca este módulo ao:**
- Receber equipamento na portaria do lab (US-EQP-006): registra `condicao_visual_chegada` + ≥1 foto + lacre + checklist de anomalias.
- Cadastrar equipamento se cliente trouxe instrumento novo (sem cadastro prévio) — US-EQP-001 com fluxo de cadastro provisório.
- Imprimir etiqueta com TAG provisória de bancada para facilitar identificação durante calibração.
- Registrar devolução física ao cliente com `condicao_visual_devolucao` + foto + `termo_devolucao_assinado_url`.
- Decidir entre `prosseguir / contatar_cliente / recusar / prosseguir_com_ressalva` quando condição != integro (com justificativa ≥30 chars).

**Frequência:** diária (cada entrada física de equipamento).
**Device:** web desktop na portaria do lab; câmera do navegador pra foto.

**Permissões (action AuthorizationProvider):**
- `equipamento.criar` ✅
- `equipamento.ler` ✅
- `equipamento.imprimir_etiqueta` ✅
- `equipamento.receber_no_lab` ✅
- `equipamento.devolver` ✅
- `equipamento.editar` ❌ (só metrologista — risco INV-025)
- `equipamento.sucatear` ❌ (só metrologista/admin)
- `equipamento.transferir` ❌ (só atendente/metrologista/admin)

---

## Persona terciária: Atendente/recepção (P-COM-01)

Toca este módulo ao:
- Receber equipamento na recepção do cliente (se o lab atende sem almoxarife dedicado): confirma TAG, vincula a cliente, imprime etiqueta com QR.
- Transferir equipamento entre clientes do mesmo tenant (US-EQP-004) com aceite duplo.
- Consultar ficha 360° pra responder cliente que liga.

**Frequência:** diária.
**Device:** web desktop.

**Permissões:**
- `equipamento.criar` ✅
- `equipamento.ler` ✅ (escopo restrito — só clientes com OS aberta ou últimos 90d)
- `equipamento.transferir` ✅
- `equipamento.imprimir_etiqueta` ✅
- `equipamento.receber_no_lab` ❌ (só almoxarife/metrologista)

---

## Anti-personas

- Cliente final querendo editar dados do próprio equipamento → não tem acesso direto (Wave futura — portal-cliente pode entregar leitura ficha 360°).
- Tenant tentando alterar TAG/NS/fabricante pós-certificado → bloqueado por INV-025.
- Tenant tentando rebaixar perfil A → B pra escapar INV-025 → bloqueado por `perfil_tenant_no_momento_cadastro` snapshot (RBC B4).
- Atendente do tenant Y escaneando QR de tenant X → resposta dual-mode (Escopo B — payload mínimo sem PII; INV-051).

---

## Convenções

- Persona promovida pra `../../personas.md` (domínio) se aparecer em ≥2 módulos do domínio com mesma responsabilidade.
- Atualização de permissões → atualizar também migration `seed_authz_acoes` correspondente.
