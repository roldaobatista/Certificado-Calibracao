---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
diataxis: explanation
audiencia: agente
---

# PRD — Colaboradores (RH mínimo)

## Problema

Tenant precisa cadastrar quem trabalha pra ele com 3 objetivos no MVP-1:
1. **RBAC** — Operação/Metrologia/Financeiro consultam quem pode fazer o quê (técnico, signatário, atendente).
2. **Comissão (BIG-09)** — Financeiro precisa saber qual técnico/atendente está na OS pra calcular comissão.
3. **Matriz de habilidades** — Agenda da Operação aloca técnico capacitado pra serviço específico (balança 50kg ≠ paquímetro 0,01mm).

Hoje (planilha): cadastro duplicado, comissão calculada na mão com erro frequente (Dor financeira recorrente), técnico sem habilidade aceita OS errada.

## Goals MVP-1 (MÍNIMO)

- CRUD de colaborador (nome, CPF, e-mail, telefone, foto opcional).
- Vínculos: CLT / PJ / estagiário / sócio / terceirizado (campo livre + tabela base).
- N papéis por colaborador (técnico, signatário, atendente, gerente, dono, qualidade, motorista UMC).
- Matriz de habilidades com nível (aprendiz / capacitado / mestre).
- % de comissão por colaborador (default + override por OS).
- Anexo de documentos (CTPS, CNH, certificados) — sem gestão de validade no MVP-1.
- Desligamento = data + motivo livre (sem cálculo de rescisão).
- Dedup por CPF dentro do tenant (espelha INV-024 do cliente).

## Non-goals MVP-1 (explícitos)

- **Folha de pagamento** — Wave C ou V2.
- **eSocial** — V2.
- **Ponto eletrônico CLT** — V2. (Motorista UMC tem jornada legal no módulo frota — INV-020.)
- **Avaliação de desempenho** — V2.
- **Vagas / recrutamento / onboarding workflow** — V2.
- **Benefícios (VR, VT, plano de saúde)** — V2.
- **Gestão de validade de treinamento** — V2 (MVP-1 só anexa PDF + data).
- **Férias / banco de horas** — V2.
- **Holerite / contracheque** — V2.

## Critérios de aceitação (binários)

- [ ] AC-COL-01: Cadastrar colaborador com CPF duplicado no mesmo tenant é bloqueado (espelha INV-024).
- [ ] AC-COL-02: Colaborador sem papel não aparece em nenhum dropdown de OS / certificado.
- [ ] AC-COL-03: Atribuir papel "signatário" sem escopo declarado é bloqueado (INV-003 — escopo é em `responsabilidade-tecnica.md`).
- [ ] AC-COL-04: % comissão padrão por colaborador é aplicada quando OS é faturada; override por OS é registrado em audit (INV-001).
- [ ] AC-COL-05: Matriz de habilidades retorna ≥1 colaborador apto pra cada tipo de serviço cadastrado (ou marca "sem técnico habilitado" pro gerente).
- [ ] AC-COL-06: Desligamento revoga papéis automaticamente; colaborador inativo não aparece em dropdowns mas continua referenciado em histórico (INV-025 espírito).
- [ ] AC-COL-06-2 (ADR-0016 INV-INT-011): **Desligamento síncrono em ≤2s** — `Colaborador.Desligado` publicado com `is_rt_signatario, tipos_servico_assinava, comissoes_pendentes_count`; consumers obrigatórios reagem: (a) `acesso-seguranca` encerra sessões web + mobile JWT + bloqueia login (publica `AcessoSeguranca.SessoesEncerradasForcado`); (b) `operacao/os` marca OSs alocadas como `tecnico_desligado_pendente_reatribuicao=true` (publica `OS.PendenteReatribuicao`); (c) `financeiro/comissoes` marca comissões pendentes como `bloqueado_por_desligamento=true` (publica `Comissoes.ComissaoBloqueadaPorDesligamento`); (d) `financeiro/caixa-tecnico` marca despesas/adiantamentos "a reconciliar"; (e) `metrologia/certificados` se era RT (INV-INT-002 cobre); (f) `suporte-saas` encerra sessão remota se ativa.
- [ ] AC-COL-07: Conformidade WCAG 2.1 AA na tela de cadastro (INV-016).

## Métricas de sucesso

Ver `metricas.md`.

## Discovery / referências

- BIG-09 comissões; Persona 9 motorista UMC; Persona 16 Andréia CS L1
- INV-024 dedup; INV-003 escopo signatário; INV-016 acessibilidade
