---
owner: Roldão
revisado-em: 2026-05-22
status: draft
modulo: clientes
dominio: comercial
diataxis: explanation
audiencia: agente
---

# Reativação pós-anonimização — Módulo Clientes

> Política de tratamento de **cadastro novo com mesmo documento** (CPF/CNPJ) de cliente cuja Zona B ou C foi anonimizada (ADR-0021). Origem: Onda 4 saneamento Marco 1 — ALTO A2-CLI.

## Por que existe

ADR-0021 define 3 zonas de anonimização:
- **Zona A** — eliminação efetiva (LGPD art. 18 VI sem prejuízo regulatório).
- **Zona B** — anonimização in-place obrigatória (retenção Receita/ISO impede deletar; nome/CPF/CNPJ vira hash, registro permanece).
- **Zona C** — anonimização campo-a-campo.

**Caso real:** Cliente A (CPF X) pediu apagamento LGPD em 2025-08. Zona B aplicada (havia NF emitida pra ele em 2024, retenção fiscal 5 anos). Em 2027-03, A volta como cliente novo — quer fazer nova OS no mesmo laboratório. **O que o sistema faz?**

Comportamentos possíveis e suas consequências:
1. **Bloqueio cego** (rejeitar cadastro com mesmo CPF): viola CDC + art. 5º CF (livre iniciativa) — cliente real impedido de contratar.
2. **Aceitação cega** (criar cadastro novo sem aviso): perde rastreabilidade histórica (Receita pode ligar atendimento de 2024 com atendimento de 2027 — mesmo CPF, mesmo titular); auditor CGCRE estranha "cliente que sumiu e voltou sem registro".
3. **Política assistida com flag + aceite + bloqueio default** ← escolhido.

## Decisão de design

### Campo `documento_zona_b_anonimizado: bool` em `Cliente`

```python
class Cliente:
    # ... campos existentes ...
    documento_zona_b_anonimizado: bool = False  # default False
    documento_zona_b_anonimizado_em: datetime NULL
    documento_zona_b_anonimizado_motivo: text NULL  # "lgpd_titular_18_vi" | "lgpd_titular_18_iv" | "lgpd_caducidade"
```

Quando anonimização Zona B/C é aplicada a um cliente, **uma linha histórica imutável** registra o hash do documento original:

```python
class DocumentoAnonimizadoHistorico:
    id: UUID
    tenant_id: UUID
    documento_hash: bytes (sha256(documento_original + tenant_salt))  # NÃO reversível
    tipo: enum {CPF, CNPJ}
    cliente_id_original: UUID  # FK Cliente (anonimizado, ainda existe Zona B)
    anonimizado_em: datetime
    motivo: text
```

Hash usa **salt por tenant** (não dá pra correlacionar cross-tenant).

### Regra de cadastro novo

GIVEN usuário tenta cadastrar cliente com documento D:
1. Calcular `hash(D, tenant_salt)`.
2. Consultar `DocumentoAnonimizadoHistorico` no tenant.
3. SE existe match:
   - Bloquear cadastro com **HTTP 409 + mensagem específica:**
     > "Já existe um cadastro anterior com este documento que foi anonimizado por solicitação do titular. Para criar novo cadastro com o mesmo documento, é necessário aceite LGPD reforçado e justificativa do usuário operacional."
   - Oferecer **2 caminhos:**
     - **(a) Cancelar e procurar cliente** — caso usuário não soubesse do cadastro anterior (UX prevenção de erro);
     - **(b) Prosseguir com aceite reforçado** — exige:
       - Usuário operacional autenticado com papel `cadastro_avancado` (não atendente comum);
       - Novo aceite LGPD versionado com texto "Estou ciente de que existe cadastro anterior anonimizado e desejo iniciar relacionamento novo do zero";
       - Justificativa textual ≥30 chars do usuário operacional;
       - Flag `documento_zona_b_anonimizado = True` no novo `Cliente`;
       - Evento `Cliente.CadastroPosAnonimizacaoCriado` publicado;
       - Grava em `audit_trail.acessos_dados_cliente` com `finalidade=cadastro_pos_anonimizacao`.
4. SE não existe match: cadastro normal segue.

### Reativação de cliente em estado `ARQUIVADO_POR_SUCESSAO` ou `ARQUIVADO_POR_INATIVIDADE`

Diferente de Zona B anonimizada — esses cadastros têm dados PII intactos (ainda dentro do prazo de retenção). Reativação:
- Estado `ARQUIVADO_POR_INATIVIDADE` → `ATIVO`: usuário operacional aprova com justificativa ≥30 chars; renova aceite LGPD se o anterior tem >12 meses; sem necessidade de criar cadastro novo.
- Estado `ARQUIVADO_POR_SUCESSAO` → **NÃO pode reativar** (sucessao-societaria.md INV-CLI-SUCESSAO-002). Cliente é juridicamente outro.

### Política para Zona C (campo-a-campo)

Zona C anonimiza **alguns campos** (ex: endereço, telefone) mas mantém documento — cliente ainda é identificável. Cadastro novo com mesmo CPF/CNPJ neste caso **não dispara** a regra acima (não há "ressurreição" — cliente nunca foi anonimizado por inteiro). Comportamento: alerta UI "este cliente teve dados parcialmente anonimizados em DD/MM/AAAA — confirme se deseja restaurar ou criar novo cadastro" + permite usuário operacional escolher.

### Invariante novo

- **INV-CLI-REATIV-001:** Cliente cujo documento está em `DocumentoAnonimizadoHistorico` (Zona B ou C) **não pode ter cadastro novo criado com mesmo documento por usuário comum** — exige papel `cadastro_avancado` + aceite LGPD reforçado + justificativa ≥30 chars + evento `Cliente.CadastroPosAnonimizacaoCriado`. Tentativa por usuário comum retorna 409 com texto canônico (sem oracle cross-tenant — hash com tenant_salt evita correlação).

### Evento novo

```
Cliente.CadastroPosAnonimizacaoCriado
{
  cliente_id_novo,
  cliente_id_anonimizado,  # referência ao predecessor Zona B (mesmo tenant)
  documento_hash,
  motivo_anonimizacao_original,
  justificativa_cadastro_novo,
  aceite_lgpd_versao,
  operador_id,
  ocorrido_em
}
```

Consumers: BI (rastreio LGPD), auditoria (compliance ANPD), CGCRE (auditor pergunta "como esse cliente voltou?").

### UI

- Tela de cadastro mostra alerta em vermelho quando hash bate:
  > "ATENÇÃO: documento associado a cadastro anonimizado em DD/MM/AAAA. Prosseguir requer aprovação avançada."
- Botão "prosseguir" só fica habilitado se usuário tem papel `cadastro_avancado` (caso contrário, "solicitar aprovação ao gestor").

### Auditoria

- Toda criação `Cliente` com flag `documento_zona_b_anonimizado=True` grava trilha imutável (INV-001).
- ANPD pode solicitar relatório "quantos cadastros pós-anonimização foram criados neste tenant"; consulta direta na tabela.

---

## Non-goals

- **Restaurar dados anonimizados** — anonimização é irreversível por definição LGPD. Cadastro novo começa do zero.
- **Linkar cadastros (anonimizado + novo) na visão 360°** — separados por design. Histórico antigo permanece no cadastro anonimizado (sem PII visível); histórico novo no cadastro novo.
- **Notificar titular anonimizado** que cadastro novo foi criado — não há canal (PII foi anonimizada, não há contato).
- **Cross-tenant** — política é por tenant. Cliente que anonimizou em tenant A pode cadastrar em tenant B sem disparo (hashes com salts diferentes).

---

## Referências

- ADR-0021 (anonimização vs retenção — Zona A/B/C)
- INV-CLI-002 (política LGPD num único lar)
- LGPD art. 16 III, art. 18 VI
- Res. CD/ANPD nº 2/2022
