---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0013-pricing-composicional.md
  - docs/dominios/financeiro/modulos/billing-saas/modelo-de-dominio.md
  - docs/dominios/financeiro/modulos/billing-saas/prd.md
  - docs/arquitetura/anti-corrosion-layer.md
---

# Calculadora de Fatura — algoritmo composicional + 30 casos de teste

> **Pra quê:** detalhar o **algoritmo passo-a-passo** que calcula a fatura mensal/anual de um tenant, agregando os 7 tipos de `ComponentePrecificacao` definidos pela ADR-0013, com pseudocódigo executável + **30 casos de teste** cobrindo edge cases. Este doc é a fonte de verdade pra implementação do `domain/billing_saas/calculadora.py` quando o módulo entrar em construção. Sem esse detalhamento, agente IA escreve cálculo errado, fiscalização Receita Federal vê inconsistência preço × NF-e, cliente reclama de cobrança que não bate.

---

## Glossário rápido (pra Roldão)

| Termo | O que é |
|---|---|
| **Algoritmo** | Receita passo-a-passo que o sistema segue pra chegar no valor da fatura |
| **Pseudocódigo** | "Código simulado" — não roda, só explica a lógica em linguagem semi-humana, pra agente IA traduzir pra Python depois |
| **Edge case** | "Caso de canto" — situação rara onde o cálculo normal pode dar errado (ex: tenant com 0 usuários, addon ativado no dia 15 do mês) |
| **Pro-rata** | Cobrar só a parte proporcional do mês — ex: cliente contratou no dia 20, paga só 1/3 do mês |
| **Idempotência** | Rodar o mesmo cálculo 2x dá o mesmo resultado — não cria fatura duplicada |
| **Snapshot** | "Foto" do plano no momento da contratação — preço congelado |
| **Linha da fatura** | Cada item discriminado no PDF da fatura ("Mensalidade base", "3 usuários adicionais", etc) |

---

## 1. Visão geral do algoritmo

```
ENTRADA:
  - assinatura: Assinatura (contém plano_snapshot)
  - periodo: TimeRange (início_do_ciclo, fim_do_ciclo)
  - ciclo: "mensal" | "anual"

SAÍDA:
  - fatura: FaturaSaaS (com lista de LinhaFatura)

PASSOS:
  1. Validar idempotência (já existe fatura pra esse período?)
  2. Carregar contexto (usuários ativos, addons ativos, uso medido)
  3. Iterar componentes do snapshot em ordem:
     3.1 Calcular linhas dos componentes NÃO-desconto (base, faixa, adicional, bundle, addon, uso_variavel)
     3.2 Calcular subtotal parcial
     3.3 Calcular linhas dos componentes desconto (na ordem do snapshot)
  4. Aplicar cupons ativos (se houver)
  5. Consolidar: valor_bruto, descontos_total, valor_liquido
  6. Validar invariantes (sem valor negativo, números batem)
  7. Persistir Fatura + LinhaFaturas + marcar MeterUsoEvents como processados
  8. Publicar evento BillingSaas.FaturaGerada
```

---

## 2. Pseudocódigo principal

```python
def calcular_fatura(
    assinatura: Assinatura,
    periodo: TimeRange,
    ciclo: Ciclo,
    *,
    forcar_recalculo: bool = False,
) -> FaturaSaaS:
    """
    Calcula fatura composicional pro tenant, pro ciclo dado.
    Idempotente por (assinatura_id, periodo) — chamada repetida retorna fatura existente.
    """
    
    # PASSO 1 — IDEMPOTÊNCIA
    fatura_existente = FaturaSaaS.objects.filter(
        assinatura_id=assinatura.id,
        periodo_de=periodo.de,
        periodo_ate=periodo.ate,
        status__in=["aberta", "paga", "estornada"],
    ).first()
    
    if fatura_existente and not forcar_recalculo:
        return fatura_existente  # AC-BIL-010-12
    
    if forcar_recalculo and fatura_existente.status == "paga":
        raise FaturaImutavelError("Fatura paga não pode ser recalculada — use estorno")
    
    # PASSO 2 — CONTEXTO
    snapshot = assinatura.plano_snapshot  # JSONB com componentes congelados
    contexto = ContextoCalculo(
        tenant_id=assinatura.tenant_id,
        plano_versao=assinatura.plano_versao,
        ciclo=ciclo,
        periodo=periodo,
        usuarios_ativos=contar_usuarios(assinatura.tenant_id, periodo, snapshot.tipo_contagem_padrao),
        addons_ativos=set(assinatura.addons_ativos),
        uso_medido=agregar_meter_uso_events(assinatura.tenant_id, periodo),
        cupons_ativos=cupons_aplicaveis(assinatura, periodo),
    )
    
    # PASSO 3 — INICIAR FATURA
    fatura = FaturaSaaS.objects.create(
        tenant_id=assinatura.tenant_id,
        assinatura_id=assinatura.id,
        numero=proximo_numero_fatura(assinatura.tenant_id),  # INV-028 atômico
        plano_versao=assinatura.plano_versao,
        ciclo=ciclo,
        periodo_de=periodo.de,
        periodo_ate=periodo.ate,
        data_emissao=now(),
        data_vencimento=calcular_vencimento(periodo, snapshot.dias_pra_vencer or 7),
        status="aberta",
    )
    
    # PASSO 4 — COMPONENTES NÃO-DESCONTO (ordem do snapshot)
    for componente in snapshot.componentes_ordenados:
        if componente.tipo == "desconto":
            continue  # processa depois (precisa do subtotal)
        if not componente.ativo:
            continue
        
        linhas = calcular_linhas_do_componente(componente, contexto)
        for linha in linhas:
            fatura.add_linha(linha)
    
    subtotal_parcial = fatura.subtotal_atual()  # soma das linhas não-desconto
    
    # PASSO 5 — DESCONTOS (depois do subtotal)
    contexto.subtotal_parcial = subtotal_parcial
    for componente in snapshot.componentes_ordenados:
        if componente.tipo != "desconto":
            continue
        if not componente.ativo:
            continue
        
        linha = calcular_linha_desconto(componente, contexto)
        if linha:
            fatura.add_linha(linha)
    
    # PASSO 6 — CUPONS (após descontos automáticos)
    for cupom in contexto.cupons_ativos:
        linha = aplicar_cupom(cupom, fatura.subtotal_atual(), contexto)
        if linha:
            fatura.add_linha(linha)
    
    # PASSO 7 — CONSOLIDAR
    fatura.valor_bruto = sum(l.subtotal for l in fatura.linhas if not l.eh_desconto)
    fatura.descontos_total = abs(sum(l.subtotal for l in fatura.linhas if l.eh_desconto))
    fatura.valor_liquido = max(Money(0, snapshot.moeda), fatura.valor_bruto - fatura.descontos_total)
    
    # PASSO 8 — VALIDAR INVARIANTES
    if fatura.valor_liquido < Money(0, snapshot.moeda):
        raise FaturaInvalidaError("valor_liquido não pode ser negativo")
    
    if len(fatura.linhas) == 0:
        raise FaturaInvalidaError("fatura sem linhas é inválida")
    
    # PASSO 9 — MARCAR MeterUsoEvents COMO PROCESSADOS
    MeterUsoEvent.objects.filter(
        tenant_id=assinatura.tenant_id,
        medido_em__range=(periodo.de, periodo.ate),
        processado_em_fatura_id__isnull=True,
    ).update(processado_em_fatura_id=fatura.id)
    
    # PASSO 10 — PUBLICAR EVENTO
    outbox.publish(BillingSaas.FaturaGerada(
        tenant_id=assinatura.tenant_id,
        fatura_id=fatura.id,
        valor_liquido=fatura.valor_liquido,
        breakdown=[linha.to_event_dict() for linha in fatura.linhas],
    ))
    
    return fatura
```

---

## 3. Funções de cálculo por tipo de componente

### 3.1 `ComponenteBase` — mensalidade fixa

```python
def calcular_componente_base(comp: ComponenteBase, ctx: ContextoCalculo) -> list[LinhaFatura]:
    if ctx.ciclo == "mensal":
        valor = comp.preco_mensal
        descricao = "Mensalidade base"
    elif ctx.ciclo == "anual":
        valor = comp.preco_anual or (comp.preco_mensal * 12)
        descricao = "Anuidade base (12 meses)"
    else:
        raise CicloInvalidoError(ctx.ciclo)
    
    return [LinhaFatura(
        componente_origem=f"ComponenteBase#{comp.id}",
        descricao=descricao,
        quantidade=Decimal("1"),
        unidade="mês" if ctx.ciclo == "mensal" else "ano",
        preco_unitario=valor,
        subtotal=valor,
        eh_desconto=False,
    )]
```

### 3.2 `ComponenteFaixaUsuarios` — preço escalonado por seat

```python
def calcular_componente_faixa_usuarios(comp: ComponenteFaixaUsuarios, ctx: ContextoCalculo) -> list[LinhaFatura]:
    usuarios = ctx.usuarios_ativos  # já contado pelo tipo_contagem do componente
    linhas = []
    
    for faixa in comp.faixas:  # faixas validadas como contíguas no save do Plano
        # quantos usuários caem nesta faixa?
        teto = faixa.ate if faixa.ate is not None else usuarios
        qtd_na_faixa = max(0, min(teto, usuarios) - (faixa.de - 1))
        
        if qtd_na_faixa == 0:
            continue
        
        if faixa.preco_por_usuario == Money(0, ctx.moeda):
            # faixa "inclusa na base" — NÃO gera linha (visual mais limpo)
            # mas registra metadata pro PDF informar "X usuários inclusos"
            continue
        
        linhas.append(LinhaFatura(
            componente_origem=f"ComponenteFaixaUsuarios#{comp.id}",
            descricao=f"{qtd_na_faixa} usuário(s) (faixa {faixa.de}-{faixa.ate or '+'})",
            quantidade=Decimal(qtd_na_faixa),
            unidade="usuário",
            preco_unitario=faixa.preco_por_usuario,
            subtotal=faixa.preco_por_usuario * qtd_na_faixa,
            eh_desconto=False,
        ))
    
    return linhas
```

### 3.3 `ComponenteAdicionalUsuario` — overage simples

```python
def calcular_componente_adicional_usuario(comp: ComponenteAdicionalUsuario, ctx: ContextoCalculo) -> list[LinhaFatura]:
    usuarios = ctx.usuarios_ativos
    excesso = max(0, usuarios - comp.quantidade_inclusa)
    
    if excesso == 0:
        return []
    
    return [LinhaFatura(
        componente_origem=f"ComponenteAdicionalUsuario#{comp.id}",
        descricao=f"{excesso} usuário(s) além dos {comp.quantidade_inclusa} inclusos",
        quantidade=Decimal(excesso),
        unidade="usuário",
        preco_unitario=comp.preco_por_usuario_extra,
        subtotal=comp.preco_por_usuario_extra * excesso,
        eh_desconto=False,
    )]
```

### 3.4 `ComponenteBundleModulos` — não cobra, registra metadata

```python
def calcular_componente_bundle(comp: ComponenteBundleModulos, ctx: ContextoCalculo) -> list[LinhaFatura]:
    # Bundle NÃO gera linha cobrada (módulos já estão "inclusos na base").
    # Mas gera linha informativa com subtotal=0 pra renderizar "Inclui: módulos X, Y, Z" no PDF.
    if not comp.modulos:
        return []
    
    return [LinhaFatura(
        componente_origem=f"ComponenteBundleModulos#{comp.id}",
        descricao=f"Inclui: {', '.join(nome_legivel_modulo(m) for m in comp.modulos)}",
        quantidade=Decimal(len(comp.modulos)),
        unidade="módulo",
        preco_unitario=Money(0, ctx.moeda),
        subtotal=Money(0, ctx.moeda),
        eh_desconto=False,
    )]
```

### 3.5 `ComponenteAddon` — só cobra se ativado

```python
def calcular_componente_addon(comp: ComponenteAddon, ctx: ContextoCalculo) -> list[LinhaFatura]:
    if comp.modulo not in ctx.addons_ativos:
        return []  # addon não contratado
    
    # Pro-rata se addon ativado no meio do ciclo
    ativado_em = ctx.assinatura.addons_data_ativacao.get(comp.modulo)
    dias_total = (ctx.periodo.ate - ctx.periodo.de).days + 1
    dias_ativo = (ctx.periodo.ate - max(ativado_em, ctx.periodo.de)).days + 1
    
    preco_cheio = comp.preco_mensal if ctx.ciclo == "mensal" else (comp.preco_anual or comp.preco_mensal * 12)
    
    if dias_ativo >= dias_total:
        # addon ativo o ciclo todo
        return [LinhaFatura(
            componente_origem=f"ComponenteAddon#{comp.id}",
            descricao=f"Add-on: {nome_legivel_modulo(comp.modulo)}",
            quantidade=Decimal("1"),
            unidade="mês" if ctx.ciclo == "mensal" else "ano",
            preco_unitario=preco_cheio,
            subtotal=preco_cheio,
            eh_desconto=False,
        )]
    else:
        # pro-rata
        valor = preco_cheio * Decimal(dias_ativo) / Decimal(dias_total)
        return [LinhaFatura(
            componente_origem=f"ComponenteAddon#{comp.id}",
            descricao=f"Add-on: {nome_legivel_modulo(comp.modulo)} (pro-rata {dias_ativo}/{dias_total} dias)",
            quantidade=Decimal(dias_ativo),
            unidade="dia",
            preco_unitario=preco_cheio / Decimal(dias_total),
            subtotal=valor.quantize(Decimal("0.01")),
            eh_desconto=False,
        )]
```

### 3.6 `ComponenteUsoVariavel` — cobrança por uso acima do incluso

```python
def calcular_componente_uso_variavel(comp: ComponenteUsoVariavel, ctx: ContextoCalculo) -> list[LinhaFatura]:
    uso = ctx.uso_medido.get(comp.recurso, Decimal("0"))  # já agregado dos MeterUsoEvents
    excesso = max(Decimal("0"), uso - Decimal(comp.unidade_inclusa))
    
    if excesso == 0:
        return []
    
    return [LinhaFatura(
        componente_origem=f"ComponenteUsoVariavel:{comp.recurso}#{comp.id}",
        descricao=f"{excesso} {nome_legivel_recurso(comp.recurso)} além das {comp.unidade_inclusa} inclusas",
        quantidade=excesso,
        unidade=unidade_legivel_recurso(comp.recurso),
        preco_unitario=comp.preco_por_unidade_extra,
        subtotal=(comp.preco_por_unidade_extra * excesso).quantize(Decimal("0.01")),
        eh_desconto=False,
    )]
```

### 3.7 `ComponenteDesconto` — aplicado sobre subtotal parcial

```python
def calcular_componente_desconto(comp: ComponenteDesconto, ctx: ContextoCalculo) -> LinhaFatura | None:
    # Avalia a regra via RuleEngineProvider (porta #14 ACL)
    aplicavel = rule_engine.evaluate(
        rule_id=f"desconto_{comp.aplicavel_se}",
        context={**ctx.to_dict(), "parametro": comp.parametro},
        tenant_id=ctx.tenant_id,
    )
    
    if not aplicavel.result:
        return None
    
    # Base sobre qual aplica o desconto
    if comp.aplicar_em == "subtotal":
        base = ctx.subtotal_parcial
    elif comp.aplicar_em == "base":
        base = soma_linhas_origem("ComponenteBase")
    elif comp.aplicar_em == "usuarios":
        base = soma_linhas_origem(["ComponenteFaixaUsuarios", "ComponenteAdicionalUsuario"])
    elif comp.aplicar_em == "addons":
        base = soma_linhas_origem("ComponenteAddon")
    else:
        raise DescontoInvalidoError(comp.aplicar_em)
    
    if comp.desconto_percentual is not None:
        valor_desconto = (base * comp.desconto_percentual / Decimal("100")).quantize(Decimal("0.01"))
    elif comp.desconto_valor_fixo is not None:
        valor_desconto = min(comp.desconto_valor_fixo, base)  # nunca passar do base
    else:
        raise DescontoInvalidoError("desconto sem percentual nem valor_fixo")
    
    return LinhaFatura(
        componente_origem=f"ComponenteDesconto:{comp.aplicavel_se}#{comp.id}",
        descricao=desc_legivel_desconto(comp),
        quantidade=Decimal("1"),
        unidade="",
        preco_unitario=-valor_desconto,
        subtotal=-valor_desconto,
        eh_desconto=True,
    )
```

---

## 4. Casos de teste — 30 cenários cobrindo edges

> Cada caso vira `test_calculadora_fatura_caso_NN_descricao` em `tests/billing_saas/test_calculadora.py`. Nome do teste cita o caso. TST-004 obrigatório.

### Categoria A — Casos básicos (1-5)

**Caso 1 — Plano só com base mensal**
- Setup: `ComponenteBase(preco_mensal=R$ 200)`. Tenant sem usuários adicionais, sem uso variável, sem addon.
- Esperado: 1 linha "Mensalidade base = R$ 200". Total: R$ 200.

**Caso 2 — Plano só com base anual**
- Setup: `ComponenteBase(preco_mensal=R$ 100, preco_anual=R$ 1020)`. Ciclo = anual.
- Esperado: 1 linha "Anuidade base = R$ 1020". Total: R$ 1020.

**Caso 3 — Plano só com base, anual SEM preço definido**
- Setup: `ComponenteBase(preco_mensal=R$ 100, preco_anual=null)`. Ciclo = anual.
- Esperado: 1 linha "Anuidade base = R$ 1200" (100 × 12 — sem desconto anual). Total: R$ 1200.

**Caso 4 — Bundle só com módulos, sem cobrar**
- Setup: `ComponenteBase(R$ 100)` + `ComponenteBundleModulos([os, calibracao])`. Tenant sem mais nada.
- Esperado: 2 linhas — "Mensalidade base = R$ 100" + "Inclui: OS, Calibração = R$ 0". Total: R$ 100.

**Caso 5 — Cálculo idempotente**
- Setup: cenário do Caso 1 + chamada `calcular_fatura()` 2× consecutivas pra mesmo período.
- Esperado: 2ª chamada retorna **a mesma fatura** (mesma `id`, mesmo `numero`); nenhuma fatura nova criada.

### Categoria B — Faixas de usuários (6-11)

**Caso 6 — Tenant tem exatamente o teto da faixa inclusa**
- Setup: `ComponenteFaixaUsuarios([{1-5: R$ 0}, {6-15: R$ 35}])`. Tenant tem 5 usuários.
- Esperado: zero linhas de faixa (todos os 5 estão na faixa "R$ 0" → omitida do PDF). Total faixa: R$ 0.

**Caso 7 — Tenant cai entre duas faixas**
- Setup: `ComponenteFaixaUsuarios([{1-5: R$ 0}, {6-15: R$ 35}, {16+: R$ 25}])`. Tenant tem 8 usuários.
- Esperado: 1 linha "3 usuário(s) (faixa 6-15) = R$ 105" (8 − 5 = 3 na faixa 6-15). Total faixa: R$ 105.

**Caso 8 — Tenant ultrapassa última faixa (sem teto)**
- Setup: mesma config Caso 7. Tenant tem 20 usuários.
- Esperado: 2 linhas — "10 usuário(s) (faixa 6-15) = R$ 350" + "5 usuário(s) (faixa 16-+) = R$ 125". Total faixa: R$ 475.

**Caso 9 — Tenant com 0 usuários ativos**
- Setup: mesma config Caso 7. Tenant tem 0 usuários (acabou de criar).
- Esperado: 0 linhas de faixa. Total faixa: R$ 0.

**Caso 10 — Faixa com apenas 1 elemento (1-1 = R$ X)**
- Setup: `ComponenteFaixaUsuarios([{1-1: R$ 50}, {2+: R$ 30}])`. Tenant tem 1 usuário.
- Esperado: 1 linha "1 usuário (faixa 1-1) = R$ 50".

**Caso 11 — Faixa com gap (deve falhar na validação no save do plano, NÃO chega ao cálculo)**
- Setup: `ComponenteFaixaUsuarios([{1-5: R$ 0}, {10-15: R$ 30}])` — gap 6-9.
- Esperado: `ValidacaoFaixaError` no `save()` do Plano. Cálculo nunca executado pra esse plano.

### Categoria C — Adicional por usuário (12-13)

**Caso 12 — Adicional padrão**
- Setup: `ComponenteBase(R$ 100)` + `ComponenteAdicionalUsuario(quantidade_inclusa=3, preco_por_usuario_extra=R$ 25)`. Tenant tem 7 usuários.
- Esperado: 2 linhas — "Mensalidade base = R$ 100" + "4 usuário(s) além dos 3 inclusos = R$ 100" (4 × R$ 25). Total: R$ 200.

**Caso 13 — Adicional com tenant dentro do incluso**
- Setup: mesma config Caso 12. Tenant tem 2 usuários.
- Esperado: só 1 linha "Mensalidade base = R$ 100". Adicional NÃO gera linha. Total: R$ 100.

### Categoria D — Uso variável (14-17)

**Caso 14 — Uso variável dentro do incluso**
- Setup: `ComponenteUsoVariavel(recurso=nfse_emitidas, unidade_inclusa=100, preco_por_unidade_extra=R$ 0.80)`. Tenant emitiu 80 NFS-e no ciclo.
- Esperado: 0 linhas de uso variável.

**Caso 15 — Uso variável estoura incluso**
- Setup: mesma config Caso 14. Tenant emitiu 130 NFS-e.
- Esperado: 1 linha "30 NFS-e além das 100 inclusas = R$ 24.00".

**Caso 16 — Múltiplos `ComponenteUsoVariavel` no mesmo plano**
- Setup: 2 componentes — `(nfse_emitidas, 100, R$ 0.80)` e `(whatsapp_enviados, 500, R$ 0.10)`. Tenant emitiu 130 NFS-e + 600 WhatsApp.
- Esperado: 2 linhas — "30 NFS-e... = R$ 24.00" + "100 WhatsApp... = R$ 10.00". Total uso variável: R$ 34.

**Caso 17 — `MeterUsoEvent` duplicado (idempotência)**
- Setup: módulo fiscal publica 2× o mesmo evento `MeterUsoEvent(recurso=nfse_emitidas, referencia_externa="nfse_id_123")`.
- Esperado: constraint `UNIQUE (tenant_id, recurso, referencia_externa)` rejeita o 2º insert. Cálculo agrega só 1 unidade.

### Categoria E — Addons (18-21)

**Caso 18 — Addon ativo o ciclo todo**
- Setup: `ComponenteAddon(modulo=marketplace, preco_mensal=R$ 150)`. Tenant tem `addons_ativos=[marketplace]` desde antes do ciclo iniciar.
- Esperado: 1 linha "Add-on: Marketplace = R$ 150".

**Caso 19 — Addon não ativo**
- Setup: mesma config Caso 18 mas `addons_ativos=[]`.
- Esperado: 0 linhas de addon.

**Caso 20 — Addon ativado no meio do ciclo (pro-rata)**
- Setup: mesma config Caso 18. Tenant ativou marketplace no dia 15 de um mês de 30 dias.
- Esperado: 1 linha "Add-on: Marketplace (pro-rata 16/30 dias) = R$ 80.00" (150 × 16/30 = 80).

**Caso 21 — Addon cancelado no meio do ciclo**
- Setup: cliente tinha marketplace ativo, cancelou no dia 10 → efeito no próximo ciclo (ADR-0013).
- Esperado: ciclo atual ainda cobra cheio R$ 150 (cancelamento só vale a partir do próximo ciclo). Ciclo seguinte: 0 linhas.

### Categoria F — Descontos (22-26)

**Caso 22 — Desconto por ciclo anual**
- Setup: `ComponenteBase(R$ 100/mês, R$ 1200/ano)` + `ComponenteDesconto(aplicavel_se=ciclo_anual, desconto_percentual=15, aplicar_em=subtotal)`. Ciclo = anual.
- Esperado: 2 linhas — "Anuidade base = R$ 1200" + "Desconto pagamento anual (-15%) = -R$ 180". Total: R$ 1020.

**Caso 23 — Desconto por volume de usuários**
- Setup: `ComponenteBase(R$ 500)` + `ComponenteFaixaUsuarios([{1-50: R$ 0}])` + `ComponenteDesconto(aplicavel_se=volume_acima_de_N_usuarios, parametro={volume_acima_de: 30}, desconto_percentual=10, aplicar_em=subtotal)`. Tenant tem 35 usuários.
- Esperado: 2 linhas — "Mensalidade base = R$ 500" + "Desconto volume +30 usuários (-10%) = -R$ 50". Total: R$ 450.

**Caso 24 — Desconto NÃO aplicável (regra falha)**
- Setup: mesma config Caso 23 mas tenant tem 20 usuários.
- Esperado: 1 linha "Mensalidade base = R$ 500". Desconto NÃO gera linha. Total: R$ 500.

**Caso 25 — Múltiplos descontos cumulativos (ordem importa)**
- Setup: `ComponenteBase(R$ 1000)` + Desconto1 (`anual, -15%`) + Desconto2 (`volume_acima_de_N=30, -10%`). Ciclo anual + 35 usuários.
- Esperado: 3 linhas — "Anuidade base = R$ 12000" + "Desconto anual (-15%) sobre R$ 12000 = -R$ 1800" + "Desconto volume (-10%) sobre R$ 12000 = -R$ 1200". Total: R$ 9000.
- **NOTA:** ambos descontos aplicam sobre o **subtotal antes de descontos** (não cumulativo multiplicativo). Definição da ADR-0013: descontos são aditivos sobre a base que cada um aponta (`aplicar_em`). Pra cumulativo multiplicativo, reabrir ADR-0013.

**Caso 26 — Desconto resulta em valor_liquido negativo (deve ser bloqueado)**
- Setup: `ComponenteBase(R$ 100)` + Desconto fixo R$ 200.
- Esperado: `calcular_linha_desconto()` clampa o desconto pra no máximo o `base` (R$ 100) → linha "-R$ 100". valor_liquido = R$ 0. NÃO falha; degrada graciosamente.

### Categoria G — Snapshot e versionamento (27-29)

**Caso 27 — Plano versionado após contratação**
- Setup: Plano "pro@v1" com base R$ 100. Cliente contrata. Operador edita plano → pro@v2 com base R$ 150.
- Esperado: fatura do cliente usa snapshot v1 → R$ 100. Cliente NOVO (assina após v2) → R$ 150.

**Caso 28 — Migração explícita de versão**
- Setup: cliente em pro@v1 (R$ 100). Operador executa `migrarVersaoPlano(cliente, "pro@v2", efetivo_em=proximo_ciclo)`.
- Esperado:
  - Ciclo atual: ainda usa snapshot v1 → R$ 100.
  - Próximo ciclo: snapshot atualizado pra v2 → R$ 150.
  - `HistoricoAssinatura` ganha linha `evento=plano_migrado_versao, de_plano_versao=pro@v1, para_plano_versao=pro@v2`.

**Caso 29 — Plano deprecado mid-ciclo**
- Setup: cliente em pro@v1. Operador deprecia o plano inteiro (`deprecado_em=hoje`).
- Esperado: fatura continua sendo gerada normalmente (depreciação só remove do checkout de novos clientes; assinaturas existentes seguem). Snapshot continua funcionando.

### Categoria H — Cenário complexo combinado (30)

**Caso 30 — Plano "Pro" exemplo da ADR-0013 (cenário real completo)**
- Setup do plano:
  - `ComponenteBase(preco_mensal=R$ 350, preco_anual=R$ 3570)`
  - `ComponenteBundleModulos([os, calibracao, certificados, fiscal, contas-receber, caixa-tecnico])`
  - `ComponenteFaixaUsuarios([{1-5: R$ 0}, {6-15: R$ 35}, {16+: R$ 25}])`
  - `ComponenteUsoVariavel(nfse_emitidas, 100, R$ 0.80)`
  - `ComponenteUsoVariavel(whatsapp_enviados, 500, R$ 0.10)`
  - `ComponenteAddon(marketplace, R$ 150)`
  - `ComponenteDesconto(ciclo_anual, -15%, aplicar_em=subtotal)`
- Setup do tenant:
  - 8 usuários ativos
  - 120 NFS-e emitidas
  - 300 WhatsApp enviados
  - Marketplace ativo o mês todo
  - Ciclo = MENSAL (desconto anual NÃO aplica)
- Esperado: 5 linhas (sem desconto anual pq mensal):

| # | Descrição | Quantidade | Preço unitário | Subtotal |
|---|---|---|---|---|
| 1 | Mensalidade base | 1 | R$ 350,00 | R$ 350,00 |
| 2 | Inclui: OS, Calibração, Certificados, Fiscal, Contas a Receber, Caixa Técnico | 6 | R$ 0,00 | R$ 0,00 |
| 3 | 3 usuário(s) (faixa 6-15) | 3 | R$ 35,00 | R$ 105,00 |
| 4 | 20 NFS-e além das 100 inclusas | 20 | R$ 0,80 | R$ 16,00 |
| 5 | Add-on: Marketplace | 1 | R$ 150,00 | R$ 150,00 |

- WhatsApp NÃO gera linha (300 ≤ 500 inclusas).
- Desconto anual NÃO gera linha (ciclo = mensal).
- **valor_bruto = R$ 621,00**
- **descontos_total = R$ 0,00**
- **valor_liquido = R$ 621,00**

---

## 5. Edge cases que NÃO chegam ao cálculo (rejeitados antes)

| Cenário | Onde rejeita | Erro |
|---|---|---|
| Plano sem `ComponenteBase` E sem `ComponenteFaixaUsuarios` | `Plano.save()` | `PlanoSemPrecoBaseError` |
| Faixa com gap ou sobreposição | `ComponenteFaixaUsuarios.save()` | `ValidacaoFaixaError` |
| Bundle com módulo fora do catálogo de features | `ComponenteBundleModulos.save()` | `ModuloNaoEncontradoError` |
| Recurso de uso variável fora do catálogo | `ComponenteUsoVariavel.save()` | `RecursoNaoMensuravel Error` |
| Tentativa de recalcular fatura PAGA | `calcular_fatura()` linha 11 | `FaturaImutavelError` |
| `MeterUsoEvent` duplicado | constraint PG | `UniqueViolationError` |
| Fatura sem linhas | `calcular_fatura()` PASSO 7 | `FaturaInvalidaError` |
| valor_liquido negativo | clampa pra R$ 0 (não falha) | — |

---

## 6. Performance esperada

Conforme AC-BIL-010-11:

| Cenário | Latência alvo p95 |
|---|---|
| Plano simples (1-2 componentes) | < 200ms |
| Plano completo do Caso 30 (7 componentes + 1000 MeterUsoEvents agregados) | < 2s |
| Job batch faturando 50 tenants em paralelo | < 30s total (Celery workers paralelos) |

Otimizações obrigatórias:
- Índice composto `(tenant_id, recurso, medido_em)` em `meter_uso_events`
- Snapshot do plano lido **uma vez** no início (não consulta plano atual no banco)
- Agregação de `MeterUsoEvent` em **uma query SQL** (`GROUP BY recurso`) — não loop Python
- Contagem de usuários em query agregada (não objeto-a-objeto)
- Validação de componentes em runtime mínima — confiança no `save()` do Plano

---

## 7. Ordem de implementação sugerida

Quando módulo `billing-saas` entrar em construção (Wave A pós-Foundation), implementar nessa ordem pra ter testes verdes incrementais:

1. **Modelo de domínio** (entidades + agregados + validações no save) — sem cálculo ainda
2. **Caso 1** (base só) — implementa `ComponenteBase` + estrutura mínima do `calcular_fatura()`
3. **Caso 5** (idempotência) — implementa controle de fatura existente
4. **Casos 6-11** (faixas) — implementa `ComponenteFaixaUsuarios` com validações
5. **Casos 12-13** (adicional) — implementa `ComponenteAdicionalUsuario`
6. **Casos 14-17** (uso variável + MeterUsoEvent) — agora precisa integrar com módulos publicadores
7. **Casos 18-21** (addons + pro-rata) — integra com `Assinatura.addons_ativos`
8. **Casos 22-26** (descontos) — integra com `RuleEngineProvider` (ACL #14)
9. **Casos 27-29** (snapshot/versionamento) — testa imutabilidade
10. **Caso 30** (cenário completo) — teste de integração final

Cada passo é um PR atômico com seus testes verdes. Auditor de Qualidade revisa cada PR.

---

## 8. Como este doc evolui

- Caso de teste novo identificado em produção → adicionar com próximo número (Caso 31, 32...)
- Edge case não previsto que causou bug → adicionar caso + fix
- Componente novo (8º tipo da ADR-0013, se houver) → adicionar seção 3.8 + casos correspondentes
- Otimização de performance → atualizar seção 6 com benchmark real
- Mudança no algoritmo → reabrir ADR-0013 (mudança de cálculo = mudança contratual com tenants)

---

## 9. Referências

- ADR-0013 — Pricing composicional (decisão arquitetural)
- `modelo-de-dominio.md` v2 — entidades formais
- `prd.md` — US-BIL-009 (criação de plano) + US-BIL-010 (cálculo de fatura)
- `docs/arquitetura/anti-corrosion-layer.md` — porta #14 `RuleEngineProvider` (descontos) + #12 `AuthorizationProvider` (limites duros)
- `REGRAS-INEGOCIAVEIS.md` — INV-026 (não retroage), INV-028 (numeração sequencial), INV-038 (plano em uso não deletável), TST-004 (cada caso tem teste com nome citando o ID)
