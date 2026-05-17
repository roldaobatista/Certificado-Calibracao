---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# PRD — Módulo Planejamento de Capacidade Operacional

> **ATENÇÃO escopo:** este módulo trata capacidade DE OPERAÇÃO (técnicos, equipes, laboratórios, tipos de serviço). NÃO confundir com `docs/operacao/capacity-planning.md`, que trata capacidade de INFRAESTRUTURA técnica (CPU, banco, fila).

## 1. O que este módulo é

Painel e motor de planejamento que mostra a capacidade operacional disponível por técnico, equipe, laboratório e tipo de serviço, confronta com a demanda em fila/agenda e sinaliza gargalos antes da empresa prometer prazo que não vai cumprir. Permite simular agenda, distribuir serviços e identificar necessidade de contratação.

## 2. Por que este módulo existe

Hoje atendente promete prazo "no chute" baseado em achar que o técnico tem espaço. Resultado: técnico sobrecarregado, OS atrasada, cliente insatisfeito. Sem visão consolidada, gerente só descobre o gargalo quando o estouro já aconteceu. Este módulo move a decisão pra antes da promessa.

## 3. Personas

Ver `personas.md` deste módulo + `../personas.md` (P-OP-01 técnico, P-OP-04 gerente operações) + `docs/comum/personas.md`.

## 4. Escopo

- Cadastro de capacidade por técnico (horas/semana, dias úteis, férias, ausências)
- Cadastro de capacidade por equipe (soma + restrições)
- Cadastro de capacidade por laboratório (bancadas, equipamentos-padrão disponíveis, turnos)
- Cadastro de capacidade por tipo de serviço (qual técnico/equipe/laboratório pode executar)
- Tempo médio por tipo de OS (alimentado por histórico real + override manual)
- Cálculo automático de horas disponíveis vs ocupadas (por técnico/equipe/laboratório)
- Identificação de gargalos (recursos com ocupação > 85%)
- Previsão de demanda baseada em histórico + sazonalidade + chamados em fila
- Simulação de agenda (cenário "e se" sem afetar a real)
- Distribuição automática sugerida (humano confirma)
- Indicador de sobrecarga em tempo real
- Cálculo de capacidade futura (4, 8, 12 semanas)
- Indicação quantitativa de necessidade de contratação (delta capacidade × demanda)
- Painel de gerência consolidado
- Integração com Agenda (lê eventos), OS (lê tempo médio + previsto), Colaboradores (lê escalas/férias)

## 5. Non-goals

- Distribuição automática sem confirmação humana (sugestão sempre passível de override)
- Folha de pagamento ou ponto eletrônico (fica em RH/Colaboradores)
- Otimização matemática avançada (solver tipo OR-Tools) — heurísticas simples no MVP
- Substituir Agenda (este módulo lê; não cria evento)
- Previsão de receita (fica em Financeiro/BI)
- Recomendação automática de demitir (apenas contratar; demissão é decisão humana sensível)

## 6. User Stories

- **US-CPO-001:** gerente cadastra capacidade base de técnico (horas semana + dias úteis + skills)
- **US-CPO-002:** gerente cadastra capacidade do laboratório (bancadas × turnos × equipamentos)
- **US-CPO-003:** sistema calcula horas disponíveis vs ocupadas por técnico nos próximos 30 dias
- **US-CPO-004:** atendente vê, antes de prometer prazo, se há capacidade até a data X
- **US-CPO-005:** sistema sinaliza gargalo quando ocupação prevista > 85% por mais de 2 semanas
- **US-CPO-006:** gerente simula "e se eu aceitar este contrato grande" sem afetar a agenda real
- **US-CPO-007:** sistema sugere distribuição de OS entre técnicos elegíveis (humano confirma)
- **US-CPO-008:** sistema mostra tempo médio realizado por tipo de OS (vs previsto)
- **US-CPO-009:** sistema projeta capacidade futura 8 semanas considerando férias/ausências
- **US-CPO-010:** sistema indica quantos técnicos adicionais resolveriam o gargalo (delta)
- **US-CPO-011:** gerente vê painel consolidado por equipe e laboratório

## 7. Métricas

Ver `metricas.md`. Primárias: % de promessas de prazo cumpridas, % de OS distribuída via sugestão aceita, antecedência média de detecção de gargalo.

## 8. NFR

- Cálculo do painel em < 2s p95 (com cache)
- Recalcular após mudança em Agenda/OS em < 60s
- WCAG AA
- LGPD: dados de ausência/férias são pessoais; mascarar conforme RAT

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo `US-CPO-NNN`. Solver/otimização avançada exige ADR específica.
