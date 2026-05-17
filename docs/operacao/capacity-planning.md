---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Capacity planning

> ⏸️ **DORMENTE (2026-05-17):** capacity só importa quando houver servidor remoto. Em local, máquina do Roldão dita capacidade. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** projetar quantos tenants cabem na infra antes de saturar.

---

## Infra inicial (decisão fundadora — `discovery/sintese-final.md`)

- **Hostinger VPS KVM 4:**
  - 4 vCPU
  - 16 GB RAM
  - 200 GB SSD NVMe
  - 4 TB tráfego/mês
  - Localização: SP/BR
- **Backblaze B2 EU Central:** ~R$ 30/TB armazenado, R$ 50/TB egress (estimativa)
- **AWS KMS sa-east-1 + us-east-1:** $1/chave/mês + $0.03/10k requests

**Custo base estimado (sem tenants):** ~R$ 350/mês.

---

## Estimativa de consumo por tenant

(Refinar quando código existir — números abaixo são hipóteses calibradas com base em concorrentes BR)

### Perfil B (núcleo MVP-1) — tenant médio
- Cliente final cadastrado: ~500
- OS/mês: ~150
- Certificados/mês: ~100
- NF-e/mês: ~50
- Storage cumulativo (PDF certificado + anexo OS): ~5 GB/ano
- Tráfego: ~30 GB/mês
- vCPU usage médio: ~5% de 1 vCPU (picos de 50% em geração de relatório)
- RAM usage: ~500 MB médio (Django worker + cache do tenant)
- Conexões PostgreSQL: ~3 ativas

### Perfil A (premium acreditado RBC)
- 2-3x perfil B em volume

### Perfil C/D (entrante / comercial)
- 0.3-0.5x perfil B em volume

---

## Teto vertical estimado da KVM 4

Com base nas hipóteses acima:

| Métrica | Limite | Tenants perfil B |
|---------|--------|-------------------|
| RAM (16 GB - 4 GB Postgres - 2 GB OS - 2 GB cache) = 8 GB pra workers | 8 GB / 500 MB | ~16 tenants concorrentes ativos |
| vCPU (4 cores, 70% target) | 2.8 cores | ~50 tenants pelo perfil de uso intermitente |
| Disco (200 GB - 50 GB sistema - 50 GB logs) = 100 GB | 100 GB / 5 GB/ano | ~20 tenants em 1 ano |
| Conexões PG (max 100 - 10 sistema) = 90 | 90 / 3 | ~30 tenants ativos simultâneos |

**Teto realista pra KVM 4 (sem otimização agressiva):** ~15-20 tenants perfil B.

---

## Plano de scale

| Tenants | Ação |
|---------|------|
| **1-15** | KVM 4 atual basta. Otimizar uso de RAM (pool de conexões, cache compartilhado). |
| **16-25** | Migrar para KVM 8 (8 vCPU, 32 GB RAM) — Hostinger upgrade in-place |
| **26-50** | Migrar para KVM 16 OU adicionar VM dedicada pra Postgres |
| **50-100** | Postgres em VM separada + read replicas + pgBouncer |
| **100-300** | Sharding por tenant_id range (ainda schema-shared, mas em múltiplas VMs) |
| **300+** | Considerar schema-per-tenant + Postgres dedicado por shard. Reaberte ADR-0001 |

---

## Sinais de saturação iminente

- vCPU médio diário > 60% por 7 dias
- RAM > 75% por 24h
- Disco > 70%
- Latência p99 subindo > 50% sem mudança de release
- Conexões PG > 70% do max
- Queries lentas (> 1s) > 5% do tráfego

Qualquer sinal acima → revisar capacity em até 7 dias + plano de migração ativo.

---

## Custo total esperado por tier

| Stage | Infra | Estimativa mês |
|-------|-------|------------------|
| Pre-MVP-1 (Foundation) | KVM 4 + B2 free | R$ 350-500 |
| MVP-1 (1-15 tenants) | KVM 4 + B2 + KMS | R$ 800-1500 |
| 16-50 tenants | KVM 8/16 + B2 + KMS + obs cloud | R$ 2.000-4.000 |
| 50-100 tenants | KVM 16 + Postgres VM separada + read replica | R$ 4.000-8.000 |
| 100-300 tenants | Sharding + VMs múltiplas | R$ 8.000-20.000 |

**Nota:** 3ª auditoria apontou Mês 12 real R$ 3.8-6.7k (não R$ 1.5k alegado originalmente). Aceito conscientemente pelo Roldão.

---

## Monitoração contínua

Painel Grafana "Capacity" mostra:
- Top tenants por uso (vCPU, RAM, disco, tráfego)
- Projeção (tendência últimos 30 dias × dias até bater 70% do limite)
- Custo mensal acumulado

Alerta SEV-2: capacidade > 70% de qualquer recurso por 7 dias seguidos.

---

## Plano de migração / sharding (esboço)

1. **Identificar tenants candidatos a migração** (top consumidores)
2. **Provisionar shard novo** (Ansible playbook)
3. **Migração com janela de manutenção** (sáb 02-05 BRT)
4. **DNS aponta pra shard novo** pra tenant alvo
5. **Drenar conexões antigas** + validar
6. **Backup full pré-migração + pós-migração** (não pular)

Estratégia detalhada após primeiro caso real (lazy — não otimização prematura).

---

## Pre-MVP-1 (estado atual)

- ✅ Infra-alvo definida (Hostinger SP)
- ⏳ Provisionamento real ainda não ocorreu
- ⏳ Métricas reais inexistentes — números acima são hipóteses
- ⏳ Painel Grafana não montado

Recalibrar este doc após 3 meses de produção com 5 tenants.

---

## Referências

- [observabilidade.md](observabilidade.md) — métricas que alimentam capacity
- [dr-plan.md](dr-plan.md) — quando capacity vira incidente
- `discovery/sintese-final.md` — hipóteses de DAP e volume por perfil
- ADR-0001 — critério de reversão schema-shared → schema-per-tenant em TAM > 5.000
