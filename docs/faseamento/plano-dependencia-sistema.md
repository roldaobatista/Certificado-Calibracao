---
owner: arquiteto-chefe
revisado-em: 2026-06-09
status: stable
---

# Plano de Dependência de Construção — ERP Aferê (55 módulos)

> **Documento autoritativo.** Resolve o grafo de dependências dos 55 módulos em 11 níveis topológicos, fixa o caminho crítico de receita e fecha as inversões de ordem detectadas por 3 auditorias adversariais + verificação no código real (2026-06-09). Onde mapa de dependências e PRD/faseamento divergem, este documento decide e aponta a emenda necessária.
>
> **Fontes verificadas no código (não na memória):** `src/infrastructure/` e `src/domain/` inspecionados em 2026-06-09. Módulos confirmados CONSTRUÍDOS: `tenant`, `multitenant`, `audit`, `authz`, `bus`, `idempotencia`, `feature_flag`, `observabilidade`, `usuario`, `clientes`, `equipamentos`, `responsavel_tecnico`, `ordens_servico`, `metrologia/{calibracao→certificados}` (calibração + padroes + escopos_cmc + procedimentos_calibracao + licencas_acreditacoes + certificados), `fiscal`, `webhook_out`. Módulos confirmados INEXISTENTES: `orcamentos`, `precificacao`, `produtos_pecas_servicos`, `configuracoes_sistema`, `contas_receber`, `estoque`, `colaboradores`, `agenda` (e demais a jusante).
>
> **ATUALIZAÇÃO 2026-06-16 (snapshot acima superado para a cadeia de receita):** já CONSTRUÍDOS desde 2026-06-09 — `configuracoes_sistema`, `produtos_pecas_servicos`, `precificacao`, `orcamentos`, `colaboradores` e **`contas_receber` (Wave A FECHADO 2026-06-16 — ADR-0084; nível 5 fecha a receita)**. Fonte viva das contagens/estado: `docs/governanca/STATUS-GERADO.md`.
>
> **ERRATA 2026-06-09 (pós-P0 de `configuracoes-sistema` — `docs/faseamento/configuracoes-sistema/T-CFG-000-investigacao.md`):** a afirmação deste plano de que **o `fiscal` contraiu dívida de numeração** (emitiu documento numerado sem o dono `SerieDocumento`) está **factualmente errada** — verificado no código: a NFS-e guarda `provider_invoice_id`, número atribuído pelo **BaaS/município**, não numerado localmente; OS e calibração já numeram com sequences próprias (ADR-0056). Logo **não há dívida de numeração**. `configuracoes-sistema` SEGUE sendo a frente #1, mas pela via **tributária** (é a casa de `Imposto`/`RegimeTributario` que precificação/fiscal/catálogo consomem) e de cadastro base (`Empresa`/`Filial`), NÃO pela numeração. Onde abaixo se lê "dívida de numeração do fiscal", considerar essa errata. Também: US-CFG-004 (RBAC) e US-CFG-014 (feature flags) JÁ têm dono (`authz`/`feature_flag`) — não reconstruir.

---

## 1. Resumo executivo (para o dono)

O sistema já tem **pronta toda a espinha técnica e toda a esteira de calibração** — desde o cadastro do cliente e do equipamento, passando pela ordem de serviço, a calibração, o certificado assinado, a licença de acreditação e a nota fiscal de serviço. O que **ainda falta para o dinheiro entrar de ponta a ponta** é a outra metade do balcão: o **cadastro do que se vende com seu preço, o orçamento, e a conta a receber com a baixa quando o cliente paga**. Hoje existe um furo de ordem: as peças que dão **preço** (configurações do sistema, catálogo de produtos/serviços e a régua de preços) foram empurradas para "depois", mas os módulos que **usam** esse preço (orçamento, conta a receber) estão marcados para "agora" — não dá para orçar sem ter de onde tirar o preço. Por isso a **próxima frente correta não é a conta a receber, e sim começar a base de preço**: primeiro `configuracoes-sistema` (numeração de documentos e impostos), depois `produtos-pecas-servicos` (o catálogo com o valor de cada item, incluindo a tabela de preço que a OS avulsa de balcão exige), depois `precificacao` em modo parcial (preço fixo e margem manual, com um custo provisório até o cálculo de custo real existir), depois `orcamentos`, e só então `contas-receber` para fechar o ciclo. São **5 módulos de receita faltando, e a conta a receber é o último deles, não o primeiro.**

---

## 2. Tabela de níveis de construção (ordem topológica completa — 55 módulos)

> Legenda da coluna "Já construído?": **JÁ** = verificado no código 2026-06-09 · **ANTECIPAR** = está em Wave B no faseamento mas precisa subir · **FALTA** = a construir na ordem indicada · **RETROFIT** = existe parcial, precisa extração/replug.

| Nível | Módulos | Por que aqui | Já construído? |
|---|---|---|---|
| **0 — Infra** | infra base (tenant/RLS, auth base, audit/WORM, bus-outbox+idempotência, feature-flag, observabilidade, KMS, storage B2); `tenant/perfil_regulatorio` (ADR-0067) | Camada sem dependência de produto; todos consomem RLS, audit WORM, `AuthorizationProvider` (ADR-0012), ContextVar `perfil_tenant`, KMS, B2. Perfil regulatório é predicate transversal de gating. | **JÁ** |
| **1 — Cadastro base** | `clientes`; `acesso-seguranca` (RBAC/MFA — expande F-B); `configuracoes-sistema`; `webhook-out` | Dependem só de infra+tenant. `clientes` é base comercial. `configuracoes-sistema` é pré-req DURO de catálogo/estoque/numeração (`SerieDocumento` INV-028, Imposto/RegimeTributario p/ ADR-0008) — está erradamente em Wave B; **fiscal (JÁ) já contraiu essa dívida**, emitindo documento sem o dono da numeração. | clientes **JÁ**; webhook-out **JÁ**; acesso-seguranca **JÁ** (F-B); **configuracoes-sistema ANTECIPAR (FALTA)** |
| **2 — Cadastro rico** | `responsabilidade-tecnica`; `certificados-digitais`; `produtos-pecas-servicos` (catálogo + valor base + **TabelaPreco**); `colaboradores`; `equipamentos` | `responsabilidade-tecnica` é pré-req duro dos metrologia. `certificados-digitais` é pré-req de certificados/fiscal/licencas. `produtos-pecas-servicos` é a base de SKU/preço. `colaboradores` é pré-req duro de 6 módulos Wave A — declarado Wave B é a inversão mais grave. | responsabilidade-tecnica **JÁ** (`src/infrastructure/responsavel_tecnico`); equipamentos **JÁ**; **certificados-digitais FALTA** (ver dívida §6); **produtos-pecas-servicos ANTECIPAR (FALTA)**; **colaboradores ANTECIPAR (FALTA)** |
| **3 — Metrologia base + preço + serviços** | `metrologia/padroes`; `metrologia/procedimentos`; `metrologia/escopos-cmc`; `metrologia/licencas-acreditacoes`; `precificacao` (modo parcial + stub de custo); `comunicacao-omnichannel`; `estoque`; `treinamentos`; `seguranca-trabalho` | Metrologia base já fechada (lê `responsavel_tecnico` + certificados-digitais). `precificacao` depende de catálogo + custeio-real; como custeio-real é tardio, entra **em modo parcial** (preço fixo/margem-alvo manual; cost-plus e preço mínimo DIFERIDOS). `estoque`/`treinamentos`/`SST` dependem de colaboradores+os+equipamentos. | padroes/procedimentos/escopos-cmc/licencas **JÁ**; **precificacao ANTECIPAR (FALTA, parcial)**; **comunicacao-omnichannel ANTECIPAR (FALTA)**; estoque/treinamentos/SST **FALTA** |
| **4 — Metrologia emissão + receita-entrada** | `metrologia/calibracao`; `metrologia/certificados` (núcleo + **hook INV-012**); `fiscal` (NFS-e); `orcamentos`; `frota` | calibração/certificados/fiscal já fechados. **`orcamentos` (ponta de receita) depende DURO de catálogo+precificacao** — só vira viável após o nível 3 antecipado. O **hook INV-012** (NC crítica bloqueia emissão) precisa ser plugado aqui, junto de certificados, mesmo antes de `qualidade` existir. | calibracao **JÁ**; certificados **JÁ** (núcleo, **sem INV-012 — gap**); fiscal **JÁ** (só lado NF); **orcamentos FALTA**; **frota FALTA** |
| **5 — Operação + receita-saída** | `agenda`; `contas-receber`; `caixa-tecnico`; `chamados`; `base-conhecimento`; `contas-pagar` | `agenda` valida INV-020 (Lei 13.103) ao atribuir técnico (plugada na OS via porta fail-open lazy). **`contas-receber` FECHA a receita** — gatilho canônico ÚNICO = **`os.concluida` enriquecido** (ADR-0084 emenda ADR-0043 §1; **não** `Certificado.Emitido`) → `Titulo` (=`TituloEmitido`); baixa via `PaymentGatewayProvider` (Mock Wave A). **`contas-pagar` SOBE para cá** (era nível 7) porque `despesas` (nível 6) o exige duro. | **`contas-receber` JÁ (Wave A FECHADO 2026-06-16);** demais FALTAM |
| **6 — Financeiro derivado + app** | `app-tecnico`; `comissoes`; `despesas`; `billing-saas`; `contabilidade-export` | `app-tecnico` depende de os+agenda+colaboradores+estoque+caixa-tecnico. `comissoes` gatilhada por recebimento. `despesas` depende de contas-pagar(5)+caixa-tecnico. `billing-saas` depende de fiscal+acesso-seguranca+contas-receber. | **TODOS FALTAM** |
| **7 — Agregadores + comercial** | `fornecedores`; `custeio-real`; `qualidade`; `crm`; `contratos` | `custeio-real` (agregador) depende de os+estoque+comissoes+caixa-tecnico — só fecha aqui; até então `precificacao` usa stub. `qualidade` (hub NC) — **mas a trava INV-012 foi extraída para nível 4** (peça compartilhada). `fornecedores` desce para cá com contas-pagar já no nível 5. | **TODOS FALTAM** |
| **8 — Contratos+projetos+engenharia** | `sla-contratual`; `garantia`; `projetos`; `auditoria-externa`; `engenharia-tecnica`; `capacity-planning-operacional`; `onboarding`; `automacoes-bpm` (ADR-0005) | Dependem de contratos/chamados/os/qualidade. `automacoes-bpm` depende da engine ADR-0005 (ainda proposta) + catálogo de eventos de todos. | **TODOS FALTAM** |
| **9 — Leitura + plataforma** | `portal-cliente`; `relatorios-financeiros`; `gestao-documental`; `suporte-saas`; `release-management`; `integracoes-externas` | Agregadores de leitura. `relatorios-financeiros` (read-model) é o mais a jusante do financeiro. `integracoes-externas` depende da porta `OAuthClientProvider` (a criar). | **TODOS FALTAM** |
| **10 — Terminais** | `marketplace`; `bi` | `marketplace` (V2/V3) depende da cadeia inteira. `bi` (read-only) é consumidor terminal de quase todos; só útil quando todos publicam. | **TODOS FALTAM** |

---

## 3. Caminho crítico de RECEITA (cadastro → cobrança paga)

Sequência mínima para o dinheiro entrar de ponta a ponta. **Não é a conta a receber a próxima peça — são 5 módulos, e a conta a receber é o último.**

```
[N0]  infra + tenant/perfil_regulatorio                    [JÁ]
        |
[N1]  configuracoes-sistema (SerieDocumento INV-028 + Imposto/RegimeTributario)   [ANTECIPAR — FALTA]
        |  +  clientes [JÁ]
        v
[N2]  produtos-pecas-servicos (catálogo + valor_base + TabelaPreco)   [ANTECIPAR — FALTA]
        |     (sem TabelaPreco a OS avulsa US-OS-015 quebra: 422 PrecoTabelaAusente)
        v
[N3]  precificacao  (preço-fixo + margem-alvo manual; STUB de custo)   [ANTECIPAR — FALTA, parcial]
        |     (cost-plus e PREÇO MÍNIMO ficam DIFERIDOS até custeio-real N7)
        v
[N4]  orcamentos  --(Orcamento.Aprovado)-->  os [JÁ] --(consumer passivo)--> OS rascunho
        |                                       |
        |                                  (OS avulsa exige TabelaPreco vigente — 422 se faltar)
        v                                       v
   ---->  calibracao [JÁ] --(Certificado.Emitido)-->  certificados [JÁ]
                                                  |     (GATE INV-012: NC crítica bloqueia emissão → sem cert, sem NF)
                                                  v
                                            fiscal/NFS-e [JÁ — só lado NF]
                                                  |  (Fiscal.NFSeEmitida)
                                                  v
[N5]  contas-receber  (gatilho ÚNICO = os.concluida enriquecido — ADR-0084;            [JÁ — Wave A FECHADO 2026-06-16]
        |              Certificado.Emitido reconciliado/não-construído)
        |              -> Titulo (TituloEmitido); vencimento = emissão + 30; grace inadimplência por perfil)
        v
   BAIXA: PaymentGatewayProvider (Mock Wave A; Asaas real = GATE) webhook HMAC -> contas_receber.pago
        |
        +--> desbloqueio cliente (D+90 automático)  +  dispara comissoes / bi / timeline
```

**Atenção ao caso real de dogfooding (Balanças Solution):** a **calibração avulsa de balcão** precisa de fonte de preço UPSTREAM (em `orcamentos` ou na OS avulsa). Como `contas-receber` fatura pelo **valor que já vem carimbado** no evento de origem (não consulta `precificacao`), se nem catálogo (`TabelaPreco`) nem `precificacao` existirem em Wave A, o valor do serviço não tem de onde sair — quebra **antes** de chegar ao certificado. Por isso `produtos-pecas-servicos` + `precificacao` são caminho crítico, não acessório.

---

## 4. A cadeia de preço explicada

O preço **não nasce num lugar só** — ele desce por uma cadeia, e cada elo tem dono:

```
configuracoes-sistema   →   produtos-pecas-servicos   →   precificacao   →   orcamentos   →   os   →   fiscal / contas-receber
   (impostos,                (catálogo: valor_base       (TabelaPreco por      (carimba       (carimba   (faturam o valor
    SerieDocumento,           do item/serviço +           cliente/segmento +    Preco no       Preco na    JÁ CARIMBADO —
    regime tributário)        TabelaPreco vigente)        regra desconto/       orçamento)     OS)         não recalculam)
                                                          margem; cost-plus
                                                          e PREÇO MÍNIMO
                                                          dependem de custeio-real)
```

**Onde mora cada coisa (dois donos — fonte de confusão real):**
- **Valor base do item/serviço** mora em `produtos-pecas-servicos` → `ItemCatalogoVersao.preco_padrao`.
- **Tabela de preço por cliente/segmento + regra de desconto/margem** mora em `precificacao`.
- **A OS avulsa de balcão (US-OS-015) lê a `TabelaPreco` vigente NA DATA**, não o `preco_padrao` do item: se faltar entrada na tabela retorna **422 `PrecoTabelaAusente`** (AC-OS-015-2 / INV-026).

**Gap interno do próprio catálogo:** no modelo de `produtos-pecas-servicos` a entidade `TabelaPreco` está marcada **"V2 / Wave futura"** — mas a OS avulsa Wave A depende dela. **Decisão deste documento:** promover `TabelaPreco` para Wave A no `modelo-de-dominio.md`; alternativa de menor escopo é fazer a OS avulsa cair no `preco_padrao` do item como *fallback* quando não houver `TabelaPreco`. Sem uma das duas, a calibração avulsa de balcão não fecha.

**Custo e preço mínimo (anti-prejuízo):** `precificacao` **consome** custo de `custeio-real` (não calcula). Como `custeio-real` é agregador tardio (nível 7), em Wave A `precificacao` roda **PARCIAL**: só preço-fixo e margem-alvo manual. **Cost-plus e o "chão absoluto" (preço mínimo) ficam DIFERIDOS até custeio-real existir.** O contrato do stub de custo (`custo_por_item` com *fallback* configurável) é peça de nível 3; deve haver invariante de teste que **recuse publicar regra cost-plus enquanto o provider de custo for stub**, para não vender abaixo do custo silenciosamente.

---

## 5. GAPS encontrados (acionáveis)

1. **CONFLITO DE FONTE DE VERDADE (decidir e emendar — prioritário).** O PRD de `orcamentos` (`docs/dominios/comercial/modulos/orcamentos/prd.md`, linhas 69-71) declara catálogo e precificação como **GATE Wave A** (A-ORC-001 "módulo catálogo é bloqueante", A-ORC-002 "precificacao Wave A"). O faseamento canônico (`docs/faseamento-modulos.md`, linhas 87/95/98/104) coloca `precificacao`, `produtos-pecas-servicos`, `configuracoes-sistema`, `colaboradores` em **Wave B**. **Ação:** ADR/emenda alinhando os dois — recomendação é alinhar pelo PRD (subir tudo para Wave A), pois `orcamentos` já é Wave A e não funciona sem eles.

2. **`configuracoes-sistema` em ordem errada.** Pré-req DURO de catálogo (preço/impostos), estoque (multi-depósito/mínimo) e de TODO emissor de documento numerado (`SerieDocumento` INV-028). Declarado Wave B; consumidores em Wave A. **`fiscal` (JÁ construído) já emitiu documento sem o dono da numeração** — dívida já contraída. **Ação:** subir para nível 1.

3. **`produtos-pecas-servicos` + `TabelaPreco` diferidos.** A entidade `TabelaPreco` está "V2" no modelo de domínio, mas a OS avulsa Wave A a exige (422 sem ela). **Ação:** promover `TabelaPreco` para Wave A (ou fallback `preco_padrao`); subir o módulo para nível 2.

4. **`colaboradores` em ordem errada (inversão mais grave do grafo).** Pré-req DURO de `agenda`, `app-tecnico`, `treinamentos`, `SST`, `frota`, `comissoes` (6 módulos, vários já Wave A). Declarado Wave B. **Sub-conflito:** `colaboradores` lista `calibracao` como pré-req (seed `CatalogoHabilidade`). **Ação:** (a) tornar o seed `CatalogoHabilidade` um seed estático de `configuracoes-sistema` (não dependência de runtime de calibração) — opção limpa; OU (b) dividir em `colaboradores-base` (nível 2) e `colaboradores-habilidades-metrologicas` (nível ≥4). Subir para nível 2 com a opção (a).

5. **Trava INV-012 (qualidade) ausente na emissão de certificado — GAP DE RECEITA.** A regra "NC crítica bloqueia emissão de certificado" é produzida por `qualidade` (nível 7) mas necessária na emissão de `certificados` (nível 4, JÁ construído). **Verificado no código: o hook/predicate INV-012 NÃO está em `metrologia/certificados`.** Certificado bloqueado por NC = NF não emite = título não nasce → afeta receita. **Ação:** extrair só o predicate/hook INV-012 como peça compartilhada no nível 4 (fail-open lazy à la ADR-0066 até `qualidade` existir), e colocá-lo no caminho crítico como gate.

6. **`precificacao` → `custeio-real`: dependência circular de wave.** `precificacao` (Wave A, exigido por orcamentos) consome custo de `custeio-real` (Wave B, agregador a jusante). **Ação:** stub de custo no nível 3 + cost-plus/preço-mínimo diferidos + invariante que recusa cost-plus sob stub (detalhe §4).

7. **`contas-pagar` em ordem errada.** PRD diz V2/Wave C; faseamento (linha 90) diz Wave B; `despesas` (Wave B) o exige como pré-req duro. **Ação:** subir `contas-pagar` para nível 5 (com `fornecedores`), OU rebaixar a dependência `despesas → contas-pagar` para lançamento manual básico (o próprio mapa diz que estoque/despesas alimentam contas-pagar mas são opcionais).

8. **Portas de infra externas a confirmar (saem de stub antes do ciclo fim-a-fim).** `PaymentGatewayProvider` (Asaas, ADR-0050) — sem ela a **baixa** de contas-receber não fecha. `OmniChannelProvider` (porta #10) — necessária para `comunicacao-omnichannel`/chamados/agenda. `EmailTemplateProvider` (ADR-0060, reservada) antes de `comunicacao-omnichannel`. `OAuthClientProvider` (a criar) antes de `integracoes-externas`. `LLMProvider` (ADR-0059, reservada) antes de chat IA/suporte-saas.

9. **Engine de automações (ADR-0005) ainda PROPOSTA.** Pré-req duro de `automacoes-bpm` e do motor de régua do `crm`. **Ação:** aceitar ADR-0005 antes do nível 8.

> **NOTA (2026-06-13 — colaboradores P8 / T-COL-060):** o gap #4 desta seção apontava `configuracoes-sistema` como opção de casa para o seed `CatalogoHabilidade`. Após implementação da frente `colaboradores` (spec §3 D-COL-5 / TL-COL-10 / plan.md §decisões nº 4), **a decisão foi criar o model `CatalogoHabilidade` em `src/infrastructure/colaboradores/` com seed literal global** (lista de grandezas: massa, volume, temperatura, dimensional, pressão, …) via `RunPython` na migration da frente, seguindo o molde global de `authz/0003`. Isso quebra a aresta runtime com `calibracao` sem poluir `configuracoes-sistema` com tabela de RH. A opção (a) do gap #4 foi implementada, mas com modelo próprio em `colaboradores` — não em `configuracoes-sistema`.

> **NÃO é gap:** `responsabilidade-tecnica`. Auditoria adversarial #3 + verificação no código confirmam que `src/infrastructure/responsavel_tecnico/` **JÁ existe como módulo de 1ª classe** (models `ResponsavelTecnicoTenant` + `RTCompetencia`, `predicates.py`, `services_rt.py`, `views.py`, `urls.py`, migrations) e já é consumido pelos módulos de metrologia. Nenhuma ação de criação necessária. (A premissa "conceito sem dono" das verificações iniciais estava factualmente errada — corrigida aqui.)

---

## 6. Dívidas de dependência já contraídas (construído fora de ordem) e mitigação

Respondendo honestamente à pergunta "o que foi construído antes de seus pré-requisitos":

| Dívida | O que aconteceu | Status | Mitigação |
|---|---|---|---|
| **`calibracao`(M4) antes de `escopos-cmc`(M6) e `procedimentos`(M7)** | calibração FECHADA 2026-05-27; escopos-cmc e procedimentos só 2026-05-30. Um módulo de nível 4 foi construído antes de dois pré-requisitos seus. | **QUITADA** | Paga a posteriori via predicates `cmc_cobre`/`procedimento_vigente_para` com **fail-open lazy (ADR-0066)** + replug em Wave A quando os módulos foram criados. Nada pendente. |
| **`certificados`/`fiscal` antes de `certificados-digitais`** | Ambos JÁ construídos, mas `certificados-digitais` (A3/A1 + OCSP, ADR-0046) ainda não existe como módulo. | **ABERTA** | Verificar se a emissão real rodou com porta stub. Adicionar GATE explícito `certificados-digitais-OCSP-enforce` rastreado para quando `certificados-digitais`(N2) for plugado — espelhar padrão fail-open lazy ADR-0063/0066. |
| **`fiscal` aponta para `contas-receber` inexistente** | `fiscal/views.py` comenta "contas-receber previsto"; produz `Fiscal.NFSeEmitida` sem consumidor de receita (INV-FIS-CR-001 não fecha). | **ABERTA (porta passiva)** | Aceitável como evento publicado sem consumidor. **Corrigir a afirmação errada de que "fiscal fecha NF→CR→baixa": fiscal fecha SÓ o lado NF.** A metade CR→baixa não existe e é o nível 5. |
| **`certificados` sem trava INV-012** | Verificado: predicate/hook de bloqueio por NC crítica ausente em `metrologia/certificados`. | **ABERTA (gap de receita)** | Ver gap §5.5 — extrair hook INV-012 no nível 4 com fail-open lazy. |
| **`fiscal`/emissores sem `configuracoes-sistema`/`SerieDocumento`** | `fiscal` emite documento numerado sem o dono da numeração existir. | **ABERTA** | Resolvido ao antecipar `configuracoes-sistema` para nível 1; migrar a numeração interna do fiscal para o módulo dono quando ele existir. |

**Ciclos resolvidos (corretos no estado atual, manter):**
- `os ⇄ agenda`: OS já construída com **consumer passivo** (`Orcamento.Aprovado`) e porta stub para INV-020; `agenda` pluga a validação Lei 13.103 depois (fail-open lazy). **Ajuste de mapa:** reclassificar a aresta `os → agenda` de "dura" para "evento/fraco" (o mapa declara dura, o que faz a auditoria topológica falhar; o tratamento real é fraco).
- `clientes ⇄ contas-receber`: `clientes` (M1) construído com bloqueio manual; o bloqueio automático D+90 pluga quando `contas-receber` existir. **Ajuste de mapa:** reclassificar `clientes → contas-receber` de "dura" para "evento/fraco" (idem).
- `precificacao ⇄ orcamentos ⇄ custeio-real`: resolvido por stub de custo + acoplamento por evento (`HistoricoPrecoPraticado` alimentado por `Orcamento.Convertido`, não síncrono).

---

## 7. Próximas 5 frentes recomendadas (em ordem)

| # | Frente | Por que esta, agora | Pré-condição |
|---|---|---|---|
| **1** | **`configuracoes-sistema`** | Base de `SerieDocumento` (INV-028), Imposto e RegimeTributario. Pré-req duro de catálogo, estoque e de todo emissor de documento — **fiscal já contraiu essa dívida**. É a raiz da cadeia de preço e não depende de nada não-construído. | Apenas infra+tenant (JÁ). |
| **2** | **`produtos-pecas-servicos`** (incl. `TabelaPreco`) | Sem catálogo não há item nem `valor_base`; sem `TabelaPreco` a OS avulsa de balcão quebra (422 `PrecoTabelaAusente`). É o GATE A-ORC-001 do PRD de orçamentos. | `configuracoes-sistema` (#1). |
| **3** | **`precificacao`** (modo parcial + stub de custo) | GATE A-ORC-002 do PRD de orçamentos. Roda parcial (preço-fixo/margem-alvo manual); cost-plus e preço mínimo diferidos até `custeio-real`. Destrava `orcamentos` e a OS avulsa. | `produtos-pecas-servicos` (#2) + contrato do stub de custo. |
| **4** | **`colaboradores`** (base, seed de habilidades estático) | Inversão de ordem mais grave do grafo: pré-req duro de 6 módulos (agenda, app-tecnico, treinamentos, SST, frota, comissoes), vários já Wave A. Sem sujeito da trilha de treinamento (cl. 6.2) nem identidade do técnico no app. Seed `CatalogoHabilidade` vira estático em `configuracoes-sistema` para quebrar a aresta com `calibracao`. | `configuracoes-sistema` (#1). |
| **5** | **`orcamentos`** | Primeira ponta de receita do ciclo comercial. Consome catálogo+precificacao; produz `Orcamento.Aprovado` que a OS (JÁ, com consumer passivo) recebe. Fecha o lado de entrada do dinheiro antes de `contas-receber`. | #2 + #3 (e idealmente #1). |

> Em paralelo, sem entrar nas 5 frentes mas a rastrear como GATEs: extrair o **hook INV-012** junto da próxima evolução de certificados; confirmar **PaymentGatewayProvider** (Asaas) saindo de stub antes de `contas-receber`; abrir GATE **certificados-digitais-OCSP-enforce**.

---

## Recomendação inequívoca da PRÓXIMA frente

**Construir `configuracoes-sistema` agora.** É a raiz da cadeia de preço (numeração de documentos, impostos, regime tributário), é pré-requisito duro de catálogo/estoque/colaboradores e de todo emissor de documento numerado, **já tem uma dívida contraída pelo fiscal**, e não depende de nenhum módulo inexistente — pode começar imediatamente. Ela destrava, em sequência, `produtos-pecas-servicos` → `precificacao` → `orcamentos`, fechando o lado de **entrada** do dinheiro. **Não construir `contas-receber` em seguida** — ela é a última peça do ciclo de receita, não a primeira; só fica viável depois que orçamento e preço existirem e a porta de pagamento (Asaas) sair de stub.
