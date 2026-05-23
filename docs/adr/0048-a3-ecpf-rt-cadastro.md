---
owner: roldao
revisado-em: 2026-05-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0046-ocsp-crl-revogacao-online.md
  - docs/dominios/seguranca/modulos/certificados-digitais/prd.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
---

# ADR-0048 — Cadastro segregado de A3 e-CPF do RT + e-CPF demais signatários + e-CNPJ empresa

> **Status:** PROPOSTA (2026-05-23). Detectado pela auditoria Onda 8 (auditor regulatório 7): `licencas-acreditacoes` (US-LIC-006) cobria só e-CNPJ da empresa. Sem cadastro segregado do e-CPF do RT e demais signatários, assinatura de certificado de calibração não verifica vínculo `cpf↔usuario_id↔A3` — qualquer técnico com qualquer A3 emprestado poderia assinar.

## Contexto

Auditoria identificou 3 titularidades distintas com regras diferentes:

| Titular | Tipo cert | Uso | Exigência regulatória |
|---|---|---|---|
| Empresa tenant (CNPJ) | e-CNPJ A1/A3 | NF-e, atos fiscais empresa | Receita Federal — qualquer A3 do CNPJ |
| Responsável Técnico (CPF) | e-CPF A3 | Assinar certificado de calibração RBC | ISO 17025 6.2 + NIT-DICLA-021 — RT específico designado |
| Outros signatários (CPF) | e-CPF A3 | Laudos/declarações não-RBC | Boa prática — controle por escopo |

Misturar tudo em "certificado digital genérico" abre 3 brechas:
1. Técnico A usar A3 do RT B pra assinar (sem vínculo CPF→usuário)
2. NF-e emitida com e-CPF (deveria ser e-CNPJ)
3. Auditoria Cgcre vê `subject_cn.cpf` no certificado RBC e exige rastreamento — sistema responde "cadastro genérico"

## Decisão

Criar **3 cadastros segregados** no módulo `certificados-digitais` (PRD novo), com escopo enum e regras de uso distintas:

### `escopo: empresa` (e-CNPJ)
- Cadastro pelo admin tenant (US-CER-DIG-001)
- Valida `subject_cn.cnpj == tenant.cnpj`
- Uso permitido: NF-e (US-FIS-001), atos fiscais
- Bloqueia uso pra assinar cert calibração (RBC exige e-CPF do RT, não e-CNPJ)

### `escopo: rt_signatario` (e-CPF do RT)
- Cadastro pelo próprio RT via wizard onboarding (US-CER-DIG-002)
- Valida `subject_cn.cpf == usuario.cpf` (match exato, normalização: só dígitos)
- Valida usuário tem perfil `rt` ativo (`Usuario.perfis` em `acesso-seguranca`)
- Executa OCSP no cadastro (rejeita se revoked — ADR-0046)
- Uso permitido: assinar cert calibração RBC (US-CER-002), laudos técnicos
- Vínculo persistido: `cert.usuario_id = usuario.id` (FK)
- INV-A3-RT-001: módulo `certificados` ao receber pedido de assinatura RBC verifica `cert.escopo == rt_signatario AND cert.usuario_id == request.usuario.id AND cert.status_local == vigente`

### `escopo: signatario` (e-CPF de outros)
- Cadastro pelo signatário (US-CER-DIG-003), validação CPF↔usuario igual ao RT
- Uso permitido: declarações não-RBC, assinatura de OS interna
- Bloqueia uso pra assinar cert calibração RBC (apenas RT)

## Wizard onboarding RT

Fluxo obrigatório pra RT recém-designado:
1. Admin tenant cria/atualiza usuário com perfil `rt`
2. Sistema envia link de onboarding ao RT
3. RT plugga token A3 + abre Web PKI Lacuna (ADR-0009)
4. Wizard lê subject_cn + fingerprint do A3
5. Sistema valida: `cpf` confere, OCSP `good`, AC ICP-Brasil acreditada
6. Persiste cert + publica `CertificadoDigital.Cadastrado{escopo: rt_signatario}`
7. RT já pode assinar (gate AC-CER-DIG-002-1)

## Alternativas consideradas

1. **Manter cadastro único genérico** — REJEITADA. Brechas listadas no contexto.
2. **Permitir RT emprestar A3 (audit do empréstimo)** — REJEITADA. ICP-Brasil + MP 2.200-2 art. 6º proíbem compartilhamento de chave privada (titular é o único responsável).
3. **Cadastro só pelo admin (não wizard RT)** — REJEITADA. Admin não tem acesso ao token físico do RT; UX trava.
4. **Permitir e-CNPJ assinar cert RBC** — REJEITADA. NIT-DICLA-021 exige assinatura do **profissional RT** (pessoa física), não da empresa.

## Consequências

### Positivas
- Vínculo `cpf↔usuario↔A3` garantido em cadastro e em cada uso (INV-A3-RT-001)
- NIT-DICLA-021 atendida (RT específico assina)
- Auditoria Cgcre tem rastreabilidade direta
- Substitui US-LIC-008/009 do plano antigo (cadastro físico migra pra `certificados-digitais`)

### Negativas
- 3 fluxos de cadastro em vez de 1 (mitigado por wizard guiado)
- Onboarding RT exige token físico + Lacuna funcionando (mitigado por instruções claras)
- Migração: e-CNPJ já cadastrado em `licencas-acreditacoes` migra metadados pra `certificados-digitais` (lá permanece referência cruzada pra controle de vencimento operacional)

## Itens a fazer

- [ ] Criar módulo `certificados-digitais` (PRD pronto Onda 8)
- [ ] Wizard onboarding RT (UI + porta validação)
- [ ] INV-A3-RT-001 em REGRAS-INEGOCIAVEIS.md
- [ ] Migration: copiar e-CNPJ de `licencas-acreditacoes` pra `certificados-digitais` mantendo referência
- [ ] Atualizar US-LIC-006 em `licencas-acreditacoes/prd.md` pra apontar pra `certificados-digitais` como fonte de verdade
- [ ] Teste E2E: RT A cadastra A3 com CPF do RT B → 422 CPF_DIVERGENTE
- [ ] Teste E2E: técnico não-RT tenta assinar RBC com seu A3 → 403

## Aprovação

- [ ] Roldão (decisor)
- [ ] Consultor-RBC-ISO17025
- [ ] Auditor-segurança

## Referências

- MP 2.200-2/2001 art. 6º + 10
- NIT-DICLA-021
- ISO 17025 cl. 6.2
- ADR-0009, ADR-0046, ADR-0047
- INV-017, INV-A3-RT-001, INV-A3-OCSP-001
