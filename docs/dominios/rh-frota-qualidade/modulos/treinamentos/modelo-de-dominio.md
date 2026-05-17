---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: treinamentos
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/modelo-de-dominio.md
  - docs/dominios/rh-frota-qualidade/modulos/seguranca-trabalho/modelo-de-dominio.md
  - docs/dominios/operacao/modulos/ordens-de-servico/modelo-de-dominio.md
  - docs/dominios/calibracao/modulos/certificados/modelo-de-dominio.md
  - docs/comum/modelo-de-dominio.md
---

# Modelo de domínio — Módulo Treinamentos e Certificações Internas

> Entidades específicas. Transversais em `docs/comum/modelo-de-dominio.md`.

---

## Entidades

### TreinamentoCatalogo
- **Atributos obrigatórios:** id, tenant_id, nome, categoria (seguranca / tecnico / normativo / comportamental), sub_categoria (ex: NR-10, ISO-17025, balanca-mecanica), carga_horaria, validade_padrao_meses, ativo.
- **Atributos opcionais:** descricao, objetivos, pre_requisitos.
- **Invariantes:** `INV-001`, `INV-TENANT-001`.
- **Ciclo de vida:** rascunho → ativo → descontinuado.

### Evento (turma)
- **Atributos obrigatórios:** id, tenant_id, treinamento_catalogo_id, data_inicio, data_fim, local, facilitador_id (interno) OU facilitador_externo (texto + CPF/CNPJ opcional), carga_horaria_real, status (programado / em_andamento / concluido / cancelado).
- **Atributos opcionais:** material_anexo (lista), observacao.
- **Invariantes:** `INV-001`.
- **Ciclo de vida:** programado → em andamento → concluído → arquivado.

### Participacao
- **Atributos obrigatórios:** id, tenant_id, evento_id, colaborador_id, presenca_percentual, nota (se prova), aprovado (bool), data_registro.
- **Invariantes:** `INV-001`.

### Prova
- **Atributos obrigatórios:** id, tenant_id, evento_id, questoes (lista), nota_minima_aprovacao.
- **Atributos opcionais:** instrucoes.

### Certificado (de conclusão)
- **Atributos obrigatórios:** id, tenant_id, participacao_id, colaborador_id, treinamento_catalogo_id, evento_id, data_emissao, data_validade (calculada a partir de evento + validade_padrao_meses), pdf_url, hash_pdf, status (vigente / vencido / revogado).
- **Atributos opcionais:** assinatura_digital_payload (V2, `INV-017`).
- **Invariantes:** `INV-001` (imutável após emissão).
- **Ciclo de vida:** emitido → vigente → vencido / revogado.

### Trilha
- **Atributos obrigatórios:** id, tenant_id, escopo (funcao / cargo / equipamento_modelo / norma), referencia_escopo (FK polimórfica), versao, ativa, criada_em.
- **Atributos opcionais:** descricao.
- **Invariantes:** `INV-001`; versionada — mudança gera nova versão.
- **Ciclo de vida:** rascunho → ativa → versionada → descontinuada.

### TrilhaItem
- **Atributos obrigatórios:** trilha_id, treinamento_catalogo_id, obrigatorio (bool), ordem.

### Habilitacao (visão materializada)
- **Atributos:** colaborador_id, escopo, referencia_escopo, status (apto / a_vencer / vencido / lacuna), calculado_em.
- **Origem:** view ou tabela materializada; atualizada por eventos `CertificadoEmitido` e job de vencimento.

### BypassBloqueio
- **Atributos obrigatórios:** id, tenant_id, colaborador_id, escopo, referencia_escopo, justificativa, aprovador_id, data, expira_em.
- **Invariantes:** `INV-001`; requer aprovação do gerente Qualidade; expira após janela.

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| TreinamentoCatalogo | TrilhaItem (referenciado) | `INV-001` |
| Evento | Participacao, Prova | `INV-001`, presença mínima |
| Certificado | (terminal) | `INV-001`, imutável pós-emissão |
| Trilha | TrilhaItem | `INV-001`, versionada |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| ValidadeCertificado | Data + meses padrão | Sim |
| NotaProva | Nota numérica + escala | Sim |
| HashPDFCertificado | SHA-256 do PDF emitido | Sim |
| EscopoTrilha | Tipo + referência polimórfica | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `Treinamentos.EventoConcluido` | Evento muda para "concluído" | `{tenant_id, evento_id, participantes_aprovados}` | colaboradores, RH |
| `Treinamentos.CertificadoEmitido` | Certificado emitido | `{tenant_id, certificado_id, colaborador_id, escopo}` | seguranca-trabalho, qualidade, operacao |
| `Treinamentos.CertificadoVencendo` | Job diário (30/60/90 dias) | `{tenant_id, certificado_id, validade}` | RH, colaborador |
| `Treinamentos.CertificadoVencido` | Job diário | `{tenant_id, certificado_id, colaborador_id}` | operacao (bloqueio), qualidade |
| `Treinamentos.BypassExecutado` | Bypass aprovado | `{tenant_id, colaborador_id, aprovador, justificativa}` | governanca, auditoria |
| `Treinamentos.TrilhaVersionada` | Nova versão de trilha | `{tenant_id, trilha_id, nova_versao}` | operacao, qualidade |

---

## Comandos (entradas no módulo)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `cadastrarTreinamento` | API/UI | dados mínimos | catálogo ativo |
| `programarEvento` | API/UI | treinamento ativo + facilitador | evento programado |
| `registrarPresencaENota` | API/UI | evento em andamento ou concluído | Participacao atualizada |
| `emitirCertificado` | API/UI | aprovado (presença + nota) | Certificado imutável |
| `definirTrilha` | API/UI | escopo válido | Trilha ativa versionada |
| `consultarHabilitacao` | API (operacao consulta antes de OS) | colaborador + escopo | status `apto/lacuna/vencido` |
| `executarBypass` | API/UI | aprovador autorizado | Bypass válido por janela |

---

## Integração com ISO 17025 cl. 6.2

A entidade `Habilitacao` é a evidência objetiva auditável de competência:
- Auditor CGCRE solicita matriz → módulo exporta consolidado.
- Certificado de calibração (módulo `calibracao/certificados`) consulta `Habilitacao` antes de permitir emissão e antes de aceitar signatário (`INV-003`).

---

## Schema físico

Ver `../schema-banco.md` (a criar) — segue ADR-0002 (RLS por tenant_id).

## Como este modelo evolui

- Entidade nova → verificar fronteira em `governanca-modelo-comum.md`.
- Trilha mudou → versionar; colaboradores ficam na versão antiga até renovação.
