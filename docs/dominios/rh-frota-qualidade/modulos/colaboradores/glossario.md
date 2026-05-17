---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Glossário — Colaboradores (RH mínimo)

| Termo | Definição |
|---|---|
| **Colaborador** | Pessoa física vinculada ao tenant (CLT, PJ, estagiário, sócio). MVP-1 = cadastro mínimo, sem folha. |
| **Papel** | Função que o colaborador exerce no sistema (técnico, signatário, atendente, gerente, dono, motorista UMC, qualidade). Um colaborador pode ter N papéis. |
| **Matriz de habilidades** | Tabela colaborador × habilidade técnica (ex: "calibração de balança até 50kg", "MIG/MAG"). Usada por agenda pra alocar técnico capacitado. |
| **Habilidade** | Competência técnica registrada (livre + sugerida do catálogo). Cada habilidade tem nível: aprendiz, capacitado, mestre. |
| **Vínculo** | Tipo de relação com tenant: CLT, PJ, estagiário, sócio, terceirizado. MVP-1 só armazena; cálculo de tributo = V2. |
| **Comissão** | % sobre OS faturada paga ao técnico/atendente. Liquidação = Financeiro. Cálculo = aqui (BIG-09). |
| **RT (Responsável Técnico)** | Colaborador signatário ISO 17025 cl. 6.2. Tem escopo de autorização (INV-003). Ver `responsabilidade-tecnica.md`. |
| **Motorista UMC** | Colaborador habilitado a dirigir UMC. Cadastro toca compliance Lei 13.103 (INV-020) — detalhe no módulo `frota`. |
| **Folha de pagamento** | **NON-GOAL MVP-1.** Wave C ou V2 com integração eSocial. |
| **eSocial** | Sistema gov de obrigações trabalhistas. **NON-GOAL MVP-1.** |
| **Ponto eletrônico** | Registro de jornada CLT. **NON-GOAL MVP-1.** Pro motorista UMC, jornada legal é registrada pelo módulo `frota` (INV-020), não como ponto CLT. |
| **Avaliação de desempenho** | **NON-GOAL MVP-1.** V2+. |
| **Vagas / recrutamento** | **NON-GOAL MVP-1.** V2+. |
| **Treinamento** | Registro de capacitação realizada (curso, palestra, dossiê interno). MVP-1 armazena PDF + data; gestão de validade = V2. |
| **Desligamento** | Marcação de saída. MVP-1 = data + motivo livre; rescisão calculada = V2 (eSocial). |
| **RBAC** | Role-Based Access Control. Papel do colaborador define permissões. Detalhe em `docs/dominios/suporte-plataforma/`. |

## Referências

- BIG-09 (comissões — `docs/discovery/jobs-to-be-done.md`)
- Persona 9 motorista UMC, Persona 16 Andréia CS L1
- INV-020 motorista UMC; INV-003 escopo signatário
