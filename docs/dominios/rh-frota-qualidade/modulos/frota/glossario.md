---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Glossário — Frota / Veículos

| Termo | Definição |
|---|---|
| **Veículo** | Bem móvel do tenant (carro, moto, van, UMC). Cadastrado com placa, modelo, ano, chassi, RENAVAM, categoria. |
| **UMC (Unidade Móvel de Calibração)** | Veículo equipado pra fazer calibração no local do cliente. Carrega padrões metrológicos. Trata-se de **veículo + laboratório móvel**. |
| **Motorista** | Colaborador habilitado a dirigir veículo do tenant. Motorista de UMC tem compliance Lei 13.103/2015 (INV-020). |
| **Jornada legal (Lei 13.103/2015)** | Regra trabalhista para motorista profissional: 11h ininterruptas entre jornadas + descanso 30min a cada 5h30 de direção. Hook valida agenda (INV-020). |
| **Tempo-espera** | Período em que motorista aguarda (carga/descarga/cliente). Conta como sobreaviso a 1/3 (CLT 235-C §9). |
| **Manutenção preventiva** | Revisão programada (km ou tempo). MVP-1 = registro + lembrete básico. |
| **Manutenção corretiva** | Conserto após falha. MVP-1 = registro + custo. |
| **Abastecimento** | Registro de combustível: data, km, litros, R$, posto. MVP-1 = registro manual. |
| **GPS / rastreamento** | Localização em tempo real. **NON-GOAL MVP-1**, V2 com integração de provedor (ADR futuro). |
| **TCO (Total Cost of Ownership)** | Custo total do veículo (aquisição + combustível + manutenção + IPVA + seguro + depreciação). **MVP-1 = só registros separados; cálculo consolidado = Wave C.** |
| **Caixa do técnico (OP3.2)** | Adiantamento em dinheiro pro técnico custear pedágio + combustível + alimentação durante viagem. Reconciliado contra registros de abastecimento + pedágio. Detalhe em módulo Financeiro. |
| **Checklist pré-viagem** | Lista de itens a verificar antes de sair (pneu, óleo, padrões calibrados, certificados a bordo). MVP-1 = checklist livre + bloqueio se item crítico não marcado. |
| **Atribuição** | Vínculo veículo × colaborador × período. Um veículo pode ter responsável fixo ou ser atribuído por OS. |
| **Multa de trânsito** | Auto de infração. MVP-1 = registro + responsabilização (quem dirigia); processo administrativo = V2. |
| **Sinistro** | Acidente / colisão. MVP-1 = registro básico; gestão de seguro = V2. |
| **Licenciamento / IPVA** | Pagamento anual. MVP-1 = registro + lembrete de validade. |
| **CRLV** | Certificado de Registro e Licenciamento do Veículo. MVP-1 = anexo PDF. |

## Referências

- BIG-08 frota + UMC + caixa do técnico (`docs/discovery/jobs-to-be-done.md`)
- OP3.2 caixa técnico Wave A (`docs/discovery/opportunity-solution-tree.md`)
- INV-020 (Lei 13.103/2015 + CLT 235-C §9)
- Persona 9 motorista UMC (`docs/discovery/personas-detalhadas.md`)
