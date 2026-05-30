---
id: ADR-0002
titulo: Herdar multi-empresa do Aferê e definir o armazenamento do cérebro (busca semântica)
status: aceita
data-proposta: 2026-05-28
data-aceite: 2026-05-29
depende-de: [ADR-0001]
bloqueia-fase: F-A
superseded-by:
owner: roldao
revisado-em: 2026-05-29
idioma: pt-BR
limite-linhas: 250
proposito: definir o isolamento multi-empresa e onde guardar a base de conhecimento/busca semântica do cérebro
---

# ADR-0002: Herdar multi-empresa do Aferê e definir o armazenamento do cérebro

> ✅ **FASE DE ARQUITETURA FECHADA — o dono declarou "arquitetura fechada" em 2026-05-29.** Este ADR está **ACEITO**.
> Decisões: RLS herdado do Aferê + pgvector + busca híbrida + **tudo na Hostinger** (ver Decisão + refinamentos).

## Contexto

A descoberta confirmou que a infra de IA é **multi-empresa** (herda do Aferê, que já tem
multi-tenant + RLS) e que o "cérebro" precisa de **busca por significado** (encontrar informação
por sentido, não só palavra exata) sobre conversas, OS, certificados, propostas e documentos.
Trata PII em domínio regulado → isolamento de dados entre empresas é inegociável (INV-TENANT).
Esta ADR decide **como garantir o isolamento** e **onde guardar a base do cérebro**.

## Opções consideradas

### Isolamento multi-empresa

#### Opção A1: Reusar o modelo do Aferê (tenant_id + RLS no PostgreSQL)
- **Prós:** mesmo padrão do ERP; isolamento forçado pelo banco; auditoria já existe; nada a inventar.
- **Contras:** acopla ao modelo do Aferê (aceitável — é a fonte de verdade).
- **Custo:** baixo.

#### Opção A2: Isolamento só na aplicação (sem RLS)
- **Prós:** simples no começo.
- **Contras:** frágil — um erro de query vaza dado entre empresas. Inaceitável para dado regulado.
- **Custo:** baixo agora, caro depois (risco de vazamento).

### Armazenamento do cérebro (busca semântica)

#### Opção B1: PostgreSQL + pgvector (reusar o banco do Aferê)
- **Prós:** um banco só; menos infra; transação junto dos dados; o plano do dono já sugere começar aqui.
- **Contras:** em escala muito alta de vetores pode ficar aquém de um banco vetorial dedicado.
- **Custo:** baixo.

#### Opção B2: Banco vetorial dedicado (ex.: Qdrant)
- **Prós:** otimizado para busca vetorial em larga escala.
- **Contras:** mais um serviço para operar; sincronizar com o Postgres; overkill no início.
- **Custo:** médio/alto.

## Decisão do dono registrada — fase de arquitetura ainda ABERTA

- **Isolamento: Opção A1** — herdar `tenant_id` + **RLS do Aferê**. Toda tabela da IA carrega
  `tenant_id`; nenhuma consulta sem filtro de empresa. Auditoria WORM como o Aferê. *(decisão técnica)*
- **Cérebro: Opção B1** — começar com **PostgreSQL + pgvector** (reusa o banco do Aferê). Migrar
  para banco vetorial dedicado só se/quando o volume provar necessidade (abrir ADR nova então). *(decisão técnica)*
- **Hospedagem: alinhada à infra REAL do Aferê (verificada 2026-05-29 em `C:/projetos/Certificado de calibracao`): VPS Hostinger em São Paulo + Docker Compose** — **NÃO AWS**, como eu havia suposto (corrigido). A camada de IA acompanha o Aferê no mesmo provedor (integração 100%, mesma operação; ADR-0001 do Aferê). **AWS** entra só para **KMS** (chaves criptográficas — Multi-Region Key sa-east-1 + us-east-1). **Arquivos/WORM** ficam no **Backblaze B2** via porta `StorageProvider` do Aferê — hoje **região EU Central (Europa), NÃO Brasil** ⚠️ (ponto de atenção: contradiz a narrativa "todos os dados no Brasil"; existe `WasabiBrProvider` na mesma porta para soberania BR quando um cliente exigir). O dono delegou ("o que for melhor pro sistema"); a escolha técnica é **acompanhar o Aferê**. **Exceção controlada:** processamento por LLM externo pode sair do país (ver ADR-0000) — **pseudonimização pré-LLM** obrigatória (nenhum dado que identifica a pessoa sai cru).
- **DECISÃO DO DONO (2026-05-29): hospedar TUDO na Hostinger** (mesmo provedor do Aferê — simplicidade + Brasil + custo), aberta a revisar só se um ponto técnico atrapalhar. **Avaliação técnica do agente: viável e recomendado.** A porta `HostingTarget` do Aferê já tem Hostinger como 1ª opção (Hetzner/AWS como fallback). **Único ponto a vigiar:** a **transcrição de áudio (whisper) é CPU-intensiva** — no volume inicial roda no CPU do próprio VPS; quando escalar (muitos tenants), sobe para um **VPS Hostinger dedicado/maior** (sem sair da Hostinger — eles têm planos maiores). **Não é bloqueador.** GPU dedicada é o único cenário em que a Hostinger é mais limitada que AWS/GCP, mas só importa se a transcrição em GPU virar necessidade real (volume muito alto) — aí se reavalia. **Arquivos:** hoje o Aferê usa Backblaze B2 (EU); para "tudo no Brasil" de verdade, trocar pela porta `StorageProvider` para Wasabi BR ou storage da Hostinger.

### Refinamentos da auditoria cega (2026-05-29 — incorporados; ver `AUDITORIA-CEGA-ARQUITETURA-2026-05-29.md`)
- **Busca HÍBRIDA** (8/10): pgvector (significado) **+ full-text/BM25 do Postgres** (termo exato: código OIML, nº de portaria Inmetro, modelo, nº de série) — busca por significado pura erra termo exato; o full-text pega.
- **Namespace GLOBAL para conhecimento público** (normas OIML/Inmetro, comuns a todos) **×** **por-tenant** para docs da empresa — evita re-embedar a mesma norma por empresa e fecha pegadinha de isolamento.
- **Isolamento — armadilhas a tratar como invariante (pontos cegos da auditoria):** (1) **tier assíncrono falha FECHADO** — job Celery sem `tenant_id` na sessão **recusa** rodar (nunca varre todas as empresas); tenant_id obrigatório no payload de toda task; (2) **filtro de tenant no pgvector ANTES do ranqueamento** (senão um vizinho semântico de outra empresa vem no topo e vaza); (3) **segredos/tokens por tenant em cofre** (token WhatsApp, chave da API do Aferê) — nunca global; (4) **teste automatizado de vazamento cross-tenant como gate de CI** (empresa A lendo dado de B deve FALHAR o teste).
- **Embedding:** começar com multilíngue forte (text-embedding-3-large) ou **BGE-m3 local** (casa com "dados no Brasil"); re-embedar os 1.099 docs é barato → sem lock-in nessa escolha.

## Consequências

### Positivas
- Isolamento entre empresas garantido pelo banco (não depende de a IA "lembrar" de filtrar).
- Menos peças para operar (um Postgres só) → simples para equipe pequena.
- Pseudonimização + audit herdadas do padrão do Aferê.

### Negativas
- Acopla o cérebro ao Postgres do Aferê (aceitável; reversível com ADR futura).
- pgvector pode precisar de tuning conforme cresce.

### Reversibilidade
Alta para o cérebro (trocar pgvector→Qdrant é localizado). Baixa para abandonar RLS (e não queremos).

## Non-goals
- Não decide a stack da IA (ADR-0001) nem o LLM (ADR-0000).
- Não decide retenção/eliminação de dados (vai em `docs/conformidade/lgpd/retencao-dados.md`).

## Como validar (gates)
- [ ] Toda tabela da IA tem `tenant_id` e política RLS ativa (teste prova que empresa A não vê dado de B).
- [ ] Busca semântica funcionando com pgvector sobre ≥1 tipo de documento.
- [ ] Nenhum dado pessoal cru indexado sem pseudonimização onde aplicável.
- [ ] Armazenamento provisionado em **região Brasil**; transferência internacional só do texto pseudonimizado ao LLM (ADR-0000).

## Referências
- `docs/nao-aplica.md` (multi-empresa aplica — herda do Aferê)
- `docs/seguranca/threat-model.md`, `docs/conformidade/lgpd/` (fase-2)
- ADR-0001 (stack/integração), ADR-0000 (uso de IA)
