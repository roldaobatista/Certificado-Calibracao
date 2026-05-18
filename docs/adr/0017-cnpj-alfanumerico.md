---
owner: claude-code
revisado-em: 2026-05-18
status: stable
---

# ADR-0017 — CNPJ alfanumérico (IN RFB nº 2.229/2024)

> **Status:** **ACEITO** (18/05/2026 — Roldão). Decisão regulatória pré-Wave A — afeta o value object `Documento` antes dele ser codificado.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Gap identificado em 18/05/2026 — documentação canônica (`docs/dominios/comercial/modulos/clientes/modelo-de-dominio.md:50`, `docs/arquitetura/cross-cutting/validacao.md:59`, `docs/dominios/suporte-plataforma/modulos/fornecedores/modelo-de-dominio.md:18`) assumia CNPJ como "só dígitos". `docs/discovery/normas-e-regulacao.md` não listava a IN.
> **Depende de:** ADR-0007 (camada domínio + gerador spec→código), ADR-0002 (multi-tenancy)
> **Bloqueia:** Wave A — qualquer módulo que persista CNPJ (clientes, fornecedores, fiscal, contas-receber, contas-pagar, portal-cliente, marketplace, billing-saas, configuracoes-sistema, licencas-acreditacoes).
> **Vigência regulatória:** **julho/2026** (data exata dentro do mês ainda não confirmada pela RFB).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **CNPJ alfanumérico** | A partir de jul/2026, novos CNPJs vão poder ter **letras** misturadas com números (ex: `12.ABC.345/01DE-35`). Os já existentes continuam só com números — não mudam. |
| **Dígito verificador (DV)** | Os dois últimos números do CNPJ (`-35` no exemplo). É uma "conta de conferência" que o sistema faz pra detectar CNPJ digitado errado. A conta MUDA, mas continua sendo Módulo 11. |
| **Módulo 11** | Algoritmo matemático padrão pra calcular DV. O mesmo usado em CPF, código de barras de boleto, etc. |
| **Retrocompatível** | O algoritmo novo funciona pros CNPJs velhos (só números) sem mudar o resultado. Não precisa duas funções. |
| **VO (Value Object)** | Pedaço de dado que vale pelo conteúdo, não pela identidade. CNPJ é VO — dois VOs com o mesmo CNPJ são "iguais". |

---

## Contexto

A **Instrução Normativa RFB nº 2.229/2024** (publicada em 16/10/2024) altera o formato do CNPJ a partir de **julho/2026**. Motivação oficial: esgotamento das ~100M raízes numéricas (~60M já em uso, projeção de 6M/ano novas → ~6 anos pra acabar).

A nossa documentação não previa isso. Três pontos canônicos diziam o contrário:

1. `docs/dominios/comercial/modulos/clientes/modelo-de-dominio.md:50` — VO `Documento`: "CPF ou CNPJ normalizado (**só dígitos**)"
2. `docs/dominios/suporte-plataforma/modulos/fornecedores/modelo-de-dominio.md:18` — "CNPJ válido (algoritmo brasileiro)" (algoritmo antigo)
3. `docs/arquitetura/cross-cutting/validacao.md:59` — lib `validate-docbr` (suporte ao novo formato não confirmado em 18/05/2026)

`docs/discovery/normas-e-regulacao.md` não listava a IN.

Janela limpa: F-A só implementou VOs básicos (`src/domain/shared/value_objects.py:3-4` declara explicitamente que CPF/CNPJ ficam pra Wave A). **Custo de corrigir agora = editar 9 docs + 1 ADR. Custo de corrigir depois de codar Wave A = migração de dados + alterar regex em 10+ módulos + retreinamento dos agentes IA com o catálogo de invariantes.**

---

## Decisão

### 1. Formato do CNPJ (vigência jul/2026)

| Bloco | Tamanho | Tipo | Exemplo |
|---|---|---|---|
| Raiz | 8 caracteres | **Alfanumérico** `[A-Z0-9]` | `12ABC345` |
| Ordem do estabelecimento | 4 caracteres | **Alfanumérico** `[A-Z0-9]` | `01DE` |
| Dígitos verificadores | 2 caracteres | **Numérico** `[0-9]` | `35` |

**Total:** 14 caracteres. Regex canônica do projeto:

```
^[A-Z0-9]{12}[0-9]{2}$
```

**Letras sempre MAIÚSCULAS** na persistência (normalizar input do usuário com `.upper()` antes de validar). UI pode aceitar minúsculas mas grava maiúsculas. Comparação de igualdade é case-insensitive — `12abc34501de35` e `12ABC34501DE35` são o **mesmo** CNPJ.

### 2. Algoritmo do dígito verificador

Módulo 11 com pesos 2–9 (igual ao algoritmo antigo de CNPJ numérico). **Única diferença:** conversão de cada caractere pra valor numérico antes da multiplicação:

```python
def _char_value(c: str) -> int:
    """Tabela ASCII − 48. Reproduz comportamento antigo pra dígitos.

    '0' → 0, '1' → 1, ..., '9' → 9   (CNPJ antigo: continua igual)
    'A' → 17, 'B' → 18, ..., 'Z' → 42  (CNPJ novo)
    """
    return ord(c) - 48
```

**Retrocompatibilidade garantida por design:** `_char_value('0') == 0`, então o algoritmo novo aplicado em CNPJ antigo produz exatamente os mesmos DVs. **Uma única função valida ambos.**

Exemplo oficial Serpro: `12ABC34501DE` → DV1 = `3` → DV2 = `5` → CNPJ completo `12ABC34501DE35`.

### 3. Persistência

- **Tipo SQL:** `VARCHAR(14)` (não `CHAR(14)`, não `BIGINT`).
- **Constraint:** `CHECK (cnpj ~ '^[A-Z0-9]{12}[0-9]{2}$')`.
- **Index:** B-tree padrão. Não usar hash (precisa de range scan pra LGPD direito ao esquecimento por raiz).
- **`UNIQUE (tenant_id, cnpj)`** — INV-036 mantida. Comparação case-sensitive no banco; normalização pra maiúsculo é responsabilidade do domínio antes do persist.
- **Migration de tabelas existentes (Wave A em diante):** já nasce com `VARCHAR(14)` + regex alfanumérica. Foundation F-A não tem tabela com CNPJ ainda — sem migração retroativa.

### 4. Biblioteca de validação

**Decisão:** **não depender de `validate-docbr`** até que o suporte ao formato novo esteja confirmado em release estável. Em vez disso:

- **Implementação própria** em `src/domain/shared/value_objects.py` (VO `CNPJ`), baseada nos **códigos de referência do Serpro** (publicados em Python, Java, TypeScript em https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico).
- **Suite de testes** com casos do anexo oficial da IN + casos de borda (CNPJ antigo numérico, novo alfanumérico, DV inválido, raiz só de letras, raiz só de números, minúsculas, máscara).
- **Revisão pelo `tech-lead-saas-regulado`** antes de merge.
- **Reavaliação em Wave A+1:** se `validate-docbr` ≥ versão X lançar suporte estável + suite de testes equivalente, considerar trocar.

### 5. Apresentação (UI)

- **Máscara de input:** `99.999.999/9999-99` continua funcionando — basta aceitar `[A-Z0-9]` nas 12 primeiras posições e `[0-9]` nas 2 últimas. Componente `<DocumentoInput>` em `docs/dominios/comercial/modulos/clientes/contratos/ui.md:55` precisa atualizar.
- **Exibição:** sempre com a máscara pontuada. Persistência sem máscara.
- **Entrada do usuário:** aceitar com ou sem máscara, com ou sem maiúsculas. Normalizar antes de validar.

### 6. Integrações externas (impacto cross-cutting)

| Sistema | Ação |
|---|---|
| **FiscalProvider** (ADR-0008, PlugNotas/Focus NFe) | Confirmar com fornecedores que adapter aceita CNPJ alfanumérico até **jun/2026** (1 mês antes da vigência). Smoke test trimestral inclui caso com CNPJ alfanumérico fictício. |
| **Web PKI Lacuna** (ADR-0009, assinatura A3) | Certificado ICP-Brasil traz CNPJ do titular; aceitar leitura de alfanumérico. Validar com Lacuna pré-Wave A do fiscal. |
| **Backblaze B2 + WORM** | Sem impacto (CNPJ vai como string em metadado/payload). |
| **ViaCEP / consultas externas** | Sem impacto direto. |
| **Pix BCB** (recebimento) | BCB já confirmou suporte ao alfanumérico no payload Pix. Sem ação. |

### 7. Plano de cutover

- **Imediato (esta ADR):** patch nos docs canônicos pra remover premissa "só dígitos".
- **Wave A:** VO `CNPJ` + suite de testes nasce alfanumérica.
- **Antes de jun/2026:** validar que todos os FiscalProviders contratados aceitam alfanumérico. Smoke test trimestral inclui caso.
- **Pós-jul/2026:** monitorar primeiros 90 dias pra detectar bugs em integrações terceiras (cartórios, bancos, prefeituras lentas pra adaptar).

---

## Itens a fazer

- [ ] Patch `docs/dominios/comercial/modulos/clientes/modelo-de-dominio.md` (linhas 17, 50)
- [ ] Patch `docs/dominios/suporte-plataforma/modulos/fornecedores/modelo-de-dominio.md` (linhas 18, 65, 91)
- [ ] Patch `docs/arquitetura/cross-cutting/validacao.md` (linha 59 + nota sobre alfanumérico)
- [ ] Patch `docs/comum/glossario-roldao.md` — verbete `CNPJ alfanumérico`
- [ ] Patch `docs/dominios/comercial/modulos/clientes/contratos/ui.md` (linha 55 — `<DocumentoInput>` aceita alfanum)
- [ ] Patch `docs/discovery/normas-e-regulacao.md` — acrescentar IN RFB nº 2.229/2024 (jul/2026)
- [ ] Patch `src/domain/shared/value_objects.py` — comentário Wave A cita esta ADR
- [ ] Patch `AGENTS.md` §11 — acrescentar linha ADR-0017 + §12 — atualizar pendências
- [ ] **Wave A:** implementar VO `CNPJ` conforme §2 + suite de testes oficial Serpro
- [ ] **Wave A:** atualizar INV-036 (REGRAS-INEGOCIAVEIS.md:66) — adicionar nota "case-insensitive comparison; persistência maiúscula"
- [ ] **Pré-jun/2026:** confirmar suporte FiscalProvider + Lacuna ICP a CNPJ alfanumérico

---

## Non-goals

- **Migrar CNPJs antigos pra formato novo** — IN não exige; antigos continuam válidos pra sempre.
- **Suportar CUIT/RFC/outros tax IDs LATAM** — fica pra ADR-0008 (FiscalProvider) quando AFIPProvider/CFDIProvider forem implementados.
- **Trocar `validate-docbr` por outra lib agora** — implementação própria no VO basta; reavaliar em Wave A+1.
- **Validar regras de raiz vs filial alfanumérica** (ex: filial não pode ter raiz diferente da matriz) — regra de negócio fiscal, não escopo desta ADR.
- **Aceitar minúsculas na persistência** — sempre maiúsculas. Decisão fechada.

---

## Consequências

### Positivas
- **Pronto pra jul/2026 antes do código existir** — sem migração de dados, sem refactor de regex em N módulos.
- **Algoritmo único** valida CNPJ antigo e novo (retrocompatibilidade matemática garantida).
- **Documentação canônica corrige premissa errada** antes que agentes IA codifiquem com base nela.
- **INV-036 (CNPJ único por tenant) mantida** — só adiciona regra de normalização.

### Negativas
- **Implementação própria do DV** em vez de lib pronta — custo: 1 arquivo + suite de testes (~80 linhas estimadas). Mitigado pelo Serpro publicar referência oficial.
- **Cuidado adicional com case-insensitive** — risco de bug se algum lugar fizer comparação case-sensitive sem normalizar. Mitigado por convenção "domínio sempre normaliza pra maiúsculo antes de persistir".
- **Integrações externas podem demorar** — cartório/banco/prefeitura lentos podem rejeitar CNPJ alfanumérico nos primeiros meses pós-jul/2026. Risco residual aceito; monitoração pós-cutover detecta.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Lib pronta (`validate-docbr`) vs implementação própria | Implementação própria | Suporte ao novo formato não confirmado; código de referência Serpro disponível |
| Persistir maiúsculo vs preservar case do usuário | Maiúsculo | Norma RFB usa maiúsculo no exemplo oficial; evita ambiguidade em UNIQUE |
| `VARCHAR(14)` vs `CHAR(14)` vs `BIGINT` | `VARCHAR(14)` | Aceita letras; sem padding desnecessário |
| Validar agora vs deixar pra Wave A | Decisão agora, código em Wave A | Premissa errada na doc canônica viraria armadilha pros agentes IA na Wave A |

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| RFB adia vigência pra 2027+ | Manter ADR (custo zero; código retrocompatível continua funcionando) |
| RFB muda algoritmo do DV antes de jul/2026 | Atualizar §2 + suite de testes; sem mudança estrutural na ADR |
| `validate-docbr` lança suporte estável | Avaliar troca; manter implementação própria como fallback testado |
| Fornecedor fiscal recusa CNPJ alfanumérico pós-jul/2026 | Acionar cláusula contratual ADR-0008 §5; se não resolver em 30d, swap pra fallback |

---

## Aprovação

- [x] **Roldão (decisor):** aceita formato + algoritmo + implementação própria? — **ACEITO 18/05/2026**
- [ ] **`tech-lead-saas-regulado` (subagente):** revisa código do VO antes de merge — pendente (gatilho na Wave A)
- [ ] **`advogado-saas-regulado` (subagente):** confirma cobertura regulatória da IN — pendente
- [ ] **`consultor-rbc-iso17025` (subagente):** confirma sem impacto em certificado de calibração (campo "CNPJ do laboratório" no PDF aceita alfanumérico) — pendente

---

## Referências

- IN RFB nº 2.229/2024 — https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico
- Nota Técnica Conjunta 2025.001 (NF-e/NFS-e) — https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=5ZkvIZt10mQ%3D
- Códigos de referência Serpro (Python/Java/TypeScript) — link na página oficial RFB acima
