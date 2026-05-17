---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Modelo de domínio — Colaboradores

## Agregados

### Colaborador (agregado raiz)
- `id` (UUID), `tenant_id` (NOT NULL — INV-TENANT-002), `nome`, `cpf` (UNIQUE com tenant_id — INV-024 espelhado), `email`, `telefone`, `foto_url?`, `data_admissao`, `data_desligamento?`, `motivo_desligamento?`, `vinculo` (enum: CLT, PJ, ESTAGIARIO, SOCIO, TERCEIRIZADO), `ativo` (bool, derivado de desligamento), `comissao_default_pct` (decimal 5,2), `observacao` (text livre).
- Invariantes:
  - INV-024 espelhado: UNIQUE (tenant_id, cpf).
  - Desligamento → ativo=false → revoga todos papéis automaticamente (cascade marca `revogado_em`).
  - Colaborador inativo permanece referenciado em registros históricos (espírito INV-025).

### Papel (entidade filha)
- `id`, `colaborador_id`, `papel` (enum: TECNICO, SIGNATARIO, ATENDENTE, GERENTE, DONO, QUALIDADE, MOTORISTA_UMC), `data_inicio`, `data_fim?`, `revogado_em?`.
- Invariantes:
  - Papel SIGNATARIO requer escopo declarado em `responsabilidade_tecnica` (FK) — INV-003.
  - Papel DONO único por tenant (constraint partial unique WHERE data_fim IS NULL).
  - Papel MOTORISTA_UMC requer anexo CNH categoria válida (validação no front; cadastro permite assalvar mas marca pendência).

### Habilidade (entidade filha — matriz)
- `id`, `colaborador_id`, `habilidade_codigo` (FK catálogo), `habilidade_descricao` (livre se não-catálogo), `nivel` (enum APRENDIZ, CAPACITADO, MESTRE), `evidencia_url?` (PDF certificado), `data_avaliacao`.

### CatalogoHabilidade (entidade global, read-only pro tenant)
- Catálogo seed por tipo de serviço metrológico ([INFERÊNCIA] popular do módulo `metrologia/calibracao`).

### Documento (anexo)
- `id`, `colaborador_id`, `tipo` (CTPS, CNH, CERTIFICADO_CURSO, ASO, OUTRO), `arquivo_url`, `data_upload`, `data_validade?` (MVP-1 só armazena; alerta = V2).

## Relacionamentos
- Colaborador 1—N Papel
- Colaborador 1—N Habilidade
- Colaborador 1—N Documento
- Colaborador 1—1 ResponsabilidadeTecnica (se SIGNATARIO) — FK pro módulo `responsabilidade-tecnica` (futuro)
- Colaborador N—1 Tenant
- Colaborador (papel TECNICO/ATENDENTE) referenciado em OS (módulo Operação) — input pra comissão BIG-09

## Eventos de domínio

- `ColaboradorCadastrado` (notifica Operação pra atualizar agenda)
- `PapelAtribuido` / `PapelRevogado` (notifica Suporte-Plataforma RBAC)
- `HabilidadeAtualizada` (notifica Operação — re-elegibilidade pra OS)
- `ColaboradorDesligado` (notifica Operação + Financeiro — bloqueia novas OS + finaliza comissão pendente)

## Regras / invariantes ativas

- **INV-024 (espelhado):** dedup por CPF dentro do tenant.
- **INV-003:** signatário sem escopo = bloqueio.
- **INV-016:** acessibilidade WCAG 2.1 AA na UI.
- **INV-TENANT-001/002/003:** tenant_id obrigatório + RLS.
- **INV-001:** alteração em comissão_default_pct grava audit trail.

## Não-modelado MVP-1

Holerite, banco de horas, férias, benefícios, ponto CLT, vagas, avaliação. → V2.

## Dúvidas em aberto

- [INFERÊNCIA] Como compartilhar colaborador entre múltiplos tenants do mesmo grupo econômico? Default MVP-1 = não compartilha; reabrir em V2.
