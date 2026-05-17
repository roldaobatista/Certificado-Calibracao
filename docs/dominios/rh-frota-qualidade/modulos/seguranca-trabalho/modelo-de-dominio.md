---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/modelo-de-dominio.md
  - docs/dominios/rh-frota-qualidade/modulos/treinamentos/modelo-de-dominio.md
  - docs/dominios/operacao/modulos/ordens-de-servico/modelo-de-dominio.md
  - docs/comum/modelo-de-dominio.md
---

# Modelo de domínio — Módulo Segurança do Trabalho

> Entidades específicas. Transversais em `docs/comum/modelo-de-dominio.md`.

---

## Entidades

### EPI (Cadastro)
- **Atributos obrigatórios:** id, tenant_id, nome, nº CA, data emissão CA, validade CA, fornecedor, categoria (cabeça / olhos / ouvido / respiratório / tronco / membros / queda / pés).
- **Atributos opcionais:** foto, observação, preço unitário.
- **Invariantes de agregado:** `INV-001` (audit), `INV-TENANT-001`.
- **Ciclo de vida:** ativo → CA vencido (bloqueia entrega) → descontinuado.

### EntregaEPI
- **Atributos obrigatórios:** id, tenant_id, epi_id, colaborador_id, data_entrega, quantidade, validade_individual, termo_assinado_pdf, hash_termo, timestamp_assinatura.
- **Atributos opcionais:** observação, foto do colaborador usando o EPI.
- **Invariantes:** `INV-001` (imutável após assinatura); termo assinado obrigatório.
- **Ciclo de vida:** entregue → em uso → vencido / devolvido / extraviado.

### ASO (Atestado de Saúde Ocupacional)
- **Atributos obrigatórios:** id, tenant_id, colaborador_id, tipo (admissional / periódico / retorno / mudança função / demissional), data_emissão, validade, médico_emitente, CRM, função_avaliada, resultado (apto / inapto / apto com restrição), PDF anexado.
- **Atributos opcionais:** restrições descritas.
- **Invariantes:** `INV-001`; dado pessoal sensível LGPD (saúde) — base "obrigação legal" (NR-07).
- **Ciclo de vida:** emitido → válido → vencido → arquivado.

### TreinamentoSegurancaAplicado
- **Atributos obrigatórios:** id, tenant_id, colaborador_id, norma (NR-10 / NR-12 / NR-35 / NR-33 / outro), data_realização, carga_horária, validade, instrutor, certificado_pdf.
- **Atributos opcionais:** observação, link para evento de treinamento no módulo `treinamentos`.
- **Invariantes:** `INV-001`.
- **Ciclo de vida:** realizado → válido → vencido → renovado.

> Nota: `TreinamentoSegurancaAplicado` é a aplicação concreta a um colaborador. O catálogo e a turma vivem no módulo `treinamentos`. Aqui mantemos espelho leve por performance da regra de bloqueio.

### PermissaoTrabalho (PT)
- **Atributos obrigatórios:** id, tenant_id, os_id, tipo (altura / espaço confinado / energizado / outro), emitente_id, executante_id, data_emissão, validade_até (≤24h por padrão), descrição_serviço, medidas_controle, assinatura_emitente, assinatura_executante.
- **Atributos opcionais:** anexos (fotos).
- **Invariantes:** `INV-001`; expira automaticamente após `validade_até`.
- **Ciclo de vida:** emitida → ativa → expirada / encerrada.

### APR (Análise Preliminar de Risco)
- **Atributos obrigatórios:** id, tenant_id, os_id, template_id, campos_preenchidos (JSONB), técnico_id, data_preenchimento, assinatura.
- **Invariantes:** `INV-001` (imutável após assinatura).

### TemplateAPR
- **Atributos obrigatórios:** id, tenant_id, nome, campos (lista de pergunta + tipo + obrigatório).
- **Ciclo de vida:** rascunho → publicado → versionado → descontinuado.

### ChecklistSegurancaOS
- **Atributos obrigatórios:** id, tenant_id, os_id, template_id, respostas (JSONB), técnico_id, data_preenchimento.
- **Invariantes:** `INV-001`.

### TemplateChecklist
- **Atributos obrigatórios:** id, tenant_id, nome, aplicável_a (tipo de serviço), itens (lista).

### Acidente / QuaseAcidente
- **Atributos obrigatórios:** id, tenant_id, tipo (acidente / quase-acidente / incidente ambiental), data_hora, local, descrição, colaboradores_envolvidos (lista), evidências_fotos (lista), gravidade (leve / moderado / grave / fatal), houve_afastamento (bool), dias_afastamento, ação_corretiva_id (FK), os_id (opcional).
- **Invariantes:** `INV-001` (imutável após confirmação; adendos permitidos).

### AcaoCorretivaSST
- **Atributos obrigatórios:** id, tenant_id, acidente_id, descrição, responsável_id, prazo, status (aberta / em andamento / concluída), evidência_conclusão.

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| EPI | EntregaEPI (filhos) | `INV-001`, CA válido bloqueia entrega |
| Colaborador (em colaboradores/) | ASO, TreinamentoSegurancaAplicado (referência) | `INV-001` |
| OrdemServico (em operacao/) | PT, APR, ChecklistSegurancaOS (referências) | `INV-001` + bloqueio de execução sem checklist |
| Acidente | AcaoCorretivaSST (filhos) | `INV-001` |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| NumeroCA | Nº do Certificado de Aprovação MTE + validade | Sim |
| ValidadeASO | Data + tipo | Sim |
| HashTermo | Hash SHA-256 do PDF do termo assinado | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `SST.EPIEntregue` | EntregaEPI gravada | `{tenant_id, colaborador_id, epi_id, validade_individual}` | colaboradores, financeiro (custo) |
| `SST.ASOVencendo` | Job diário detecta ASO ≤30 dias da validade | `{tenant_id, colaborador_id, validade}` | colaboradores, notificações |
| `SST.TreinamentoSegVencendo` | Job diário detecta NR ≤30 dias | `{tenant_id, colaborador_id, norma, validade}` | treinamentos, operacao (agenda) |
| `SST.AcidenteRegistrado` | Acidente confirmado | `{tenant_id, gravidade, houve_afastamento}` | operacao, qualidade |
| `SST.OSBloqueadaSemChecklist` | Tentativa de execução sem checklist | `{tenant_id, os_id, tecnico_id}` | operacao, governanca |
| `SST.TecnicoBloqueadoSemNR` | Tentativa de alocar técnico sem NR | `{tenant_id, os_id, tecnico_id, norma}` | operacao |

---

## Comandos (entradas no módulo)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `cadastrarEPI` | API/UI | CA não vencido | EPI ativo |
| `entregarEPI` | API/UI | EPI ativo + colaborador ativo | EntregaEPI imutável + termo PDF gerado |
| `registrarASO` | API/UI | colaborador ativo + PDF anexo | ASO válido |
| `emitirPT` | API/UI | OS de risco + emitente autorizado | PT ativa |
| `preencherChecklist` | API/UI (técnico mobile) | OS atribuída ao técnico | Checklist salvo + libera execução |
| `registrarAcidente` | API/UI | dados mínimos preenchidos | Acidente imutável + evento publicado |
| `validarBloqueioTecnicoOS` | OS (consulta) | técnico + tipo OS | bool + motivo |

---

## Schema físico

Ver `../schema-banco.md` (a criar) — segue ADR-0002 (RLS por tenant_id).

## Como este modelo evolui

- Entidade nova → verificar fronteira em `governanca-modelo-comum.md`.
- Migration via janela documentada.
