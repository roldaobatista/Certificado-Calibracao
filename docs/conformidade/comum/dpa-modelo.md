---
owner: Roldão
revisado-em: 2026-05-17
status: draft
diferido_para: V2 (1º cliente externo)
---

# DPA modelo — Data Processing Agreement entre Aferê e tenant

> ⏸️ **DIFERIDO PRA V2 (2026-05-17):** sem cliente externo na janela atual, DPA não é necessário pra dogfooding Balanças Solution (mesma pessoa jurídica). Modelo abaixo é **rascunho preliminar** pra acelerar quando 1º externo aparecer. Revisão jurídica humana obrigatória antes de uso real.

---

## 1. Estrutura preliminar (rascunho)

Cláusulas padrão de DPA pra SaaS B2B regulado no Brasil:

1. **Definições** (controlador, operador, titular, dado pessoal, incidente)
2. **Objeto** — Aferê presta serviço de software; trata dados em nome do controlador
3. **Papéis** — tenant = controlador; Aferê = operador
4. **Escopo de tratamento** — operações em `lgpd-rat.md` referenciadas
5. **Obrigações do operador** (Aferê):
   - Tratar dados conforme instrução documentada do controlador
   - Manter segurança (referência a `seguranca-dados.md`)
   - Notificar incidente em 24h ao controlador
   - Não usar dado pra finalidade própria sem consentimento
   - Sigilo
   - Auxiliar nos direitos do titular (LGPD art. 18)
   - Subprocessadores listados + autorização explícita
6. **Obrigações do controlador** (tenant):
   - Ter base legal pra tratamento que pede
   - Responder solicitações de titular em 15 dias úteis
   - Não enviar dado sensível sem aviso
7. **Subprocessadores** — lista anexa (AWS, Backblaze, Anthropic, PlugNotas, etc.)
8. **Transferência internacional** — referência a `transferencia-internacional.md`
9. **Auditoria** — controlador pode auditar Aferê 1x/ano com 30d aviso + custo do controlador
10. **Vigência** — enquanto contrato Aferê-tenant vigente + retenção legal (`retencao-matriz.md`)
11. **Término** — devolução ou destruição dos dados conforme controlador escolher
12. **Crypto-shredding** — Aferê garante destruição lógica via destruição de chave KMS
13. **Lei aplicável** — Brasil
14. **Foro** — Comarca do controlador (favorece tenant)

---

## 2. Anexos obrigatórios

1. Lista de operações de tratamento (referência ao RAT)
2. Lista de subprocessadores
3. Medidas técnicas e organizacionais (referência a `seguranca-dados.md`)
4. Procedimentos de incidente (referência a `incidente-anpd-modelo.md`)
5. Procedimentos de auditoria
6. Modelo de notificação de incidente

---

## 3. Quando finalizar (ativação V2)

Quando 1º cliente externo aparecer:
- [ ] Advogado especializado em SaaS+LGPD humano revisa este rascunho (R$ 5-15k — diferido)
- [ ] Adapta a cláusulas específicas do tenant (industry específica)
- [ ] Assina (Aferê + tenant)
- [ ] Anexa lista de subprocessadores **versionada** (mudança = aviso ao tenant)

---

## 4. Auto-serviço (V2)

Idealmente, DPA é parte do onboarding self-service:
- Tenant ativa → lê DPA na própria UI → assina digitalmente
- Versões de DPA versionadas (`dpa-v1.0.0.pdf`)
- Mudança em DPA → tenants são notificados + têm prazo pra contestar

---

## 5. Casos especiais

| Caso | Tratamento |
|------|------------|
| Tenant atende cliente farma | DPA específico mais rígido (BPF, RDC ANVISA) |
| Tenant é órgão público | Cláusulas adicionais (Lei 14.129) — diferido |
| Tenant exporta dado pra fora do Brasil | Aviso explícito + escolha de provedor |

---

## 6. Pendências

- [ ] Aprovação jurídica humana (V2)
- [ ] Tradução pra inglês se houver tenant internacional
- [ ] UX self-serve no app
- [ ] Versionamento (semver DPA)

---

## 7. Referências

- LGPD lei 13.709
- `lgpd-rat.md`
- `seguranca-dados.md`
- `transferencia-internacional.md`
- `incidente-anpd-modelo.md`
- Memória `sem-cliente-externo-na-janela-atual`
