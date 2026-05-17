---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas transversais

> **Pra quê:** personas que aparecem em mais de 1 módulo. Personas específicas (técnico de campo, signatário, metrologista) ficam no `personas.md` do módulo.
>
> **Fonte rica:** `docs/discovery/personas-detalhadas.md` (16 personas). Este doc consolida só as transversais.

---

## P1 — Dono / sócio do lab ou assistência técnica

**Perfil:** 35-55 anos, técnico/engenheiro que abriu empresa. Decisor de compra de software. Stress alto com inadimplência, regulação, falta de pessoal.

**Goals no Aferê:**
- Reduzir 3+ sistemas paralelos (Bling + planilha + WhatsApp)
- Visibilidade financeira em tempo real
- Compliance regulatória (NFS-e, ISO 17025) sem ansiedade
- Reduzir esquecimento de recalibração (perde 30-50% das renovações)

**Frustrations:**
- "Pago por sistema que não entrega"
- Atendimento ruim de fornecedor
- Falta de transparência em pricing
- Customização promessa-só

**Permissões no Aferê:** Dono do tenant (papel máximo dentro do tenant).

**Quem é no MVP-1:** Roldão (Balanças Solution).

---

## P2 — Gerente operacional

**Perfil:** 30-45 anos, braço-direito do dono. Conhece processo na ponta + acompanha equipe.

**Goals:**
- Distribuir OS sem brigar com técnicos
- Acompanhar pipeline financeiro (recebimentos, inadimplência)
- Resolver "cliente liga querendo status da OS"

**Frustrations:**
- "Ferramenta nova exige mais trabalho que ajuda"
- Treinamento equipe

**Permissões:** Gerente — tudo exceto financeiro sensível + admin RBAC.

---

## P3 — Atendente / recepcionista

**Perfil:** 20-35 anos. Primeira porta. Cadastra cliente, agenda, abre OS, responde telefone/WhatsApp.

**Goals:**
- Cadastrar cliente em < 1 min
- Abrir OS sem mil cliques
- Encontrar histórico do cliente rápido
- Não perder mensagem WhatsApp

**Frustrations:**
- Cadastro duplicado entre sistemas (Dor #01)
- "Cadê a OS do Sr. Silva?"

**Permissões:** Atendente — CRM + criar OS + ver cliente + ver agenda.

---

## P4 — Financeiro

**Perfil:** 25-50 anos. Emite nota, controla cobrança, conferência.

**Goals:**
- Emitir NFS-e sem ansiedade (Dor #10)
- Conciliar pagamento ao OFX/extrato
- Cobrar inadimplente sem ofender bom pagador

**Frustrations:**
- NFS-e municipal de Vitória vs Curitiba vs SP — cada um diferente
- "Banco mudou layout do OFX outra vez"

**Permissões:** Financeiro — NFS-e + cobrança + comissões + relatórios financeiros.

---

## P5 — Auditor externo (regulador)

**Perfil:** Auditor CGCRE, fiscal estadual, ANPD (V2).

**Goals (no Aferê pelo tenant):**
- Conferir audit trail
- Verificar dossiê de validação software (ISO 17025 7.11)
- Conferir conformidade com normas

**Permissões:** Auditor read-only — acesso temporário concedido pelo Dono do tenant; auditoria reforçada.

**Quem é no MVP-1:** ninguém ainda (V2 quando 1º tenant RBC acreditado).

---

## P-COM-06 — Gestor de Pricing

**Perfil:** 30-50 anos. Dono ou gerente comercial/financeiro responsável por definir como a empresa precifica. Em empresa pequena é o próprio dono (perfil P1); em média/grande é função separada (controller, gerente comercial). Tem visão de margem e custo, conhece o mercado.

**Goals:**
- Configurar regras de formação de preço (cost-plus, margem-alvo, fixo) e versionar tabelas (pública, por segmento, por contrato).
- Definir faixas de desconto autorizadas por papel.
- Acompanhar margem média realizada vs alvo; identificar itens deficitários.
- Simular cenário de ajuste de preço (efeito em margem, na comissão do vendedor, no orçamento aberto).

**Frustrations:**
- Vendedor dando desconto no olho e fechando com margem negativa.
- Não conseguir simular "se subir 5%, quanto perco em volume".
- Mudar tabela e o sistema "perder" o histórico anterior.

**Jornada típica:** abre dashboard de margem → vê serviço X com margem 12% (alvo 25%) → investiga histórico → aperta limite de desconto de 20% pra 10% → publica nova versão da regra.

**Devices:** desktop.
**Frequência:** semanal.
**Permissões:** RBAC `gestor_pricing` — configurar regras + tabelas + faixas de desconto; leitura de margem realizada.
**Módulos onde aparece:** `comercial/precificacao` (principal), `comercial/orcamentos` (consumidor das regras), `comercial/contratos` (tabela por contrato), `financeiro/comissoes` (efeito em comissão simulada).

---

## P-BI-01 — Analista de Indicadores

**Perfil:** 25-50 anos. Pode ser o próprio dono em empresa pequena, ou perfil dedicado em empresa maior. Familiaridade média com planilhas (Excel). **Não programa SQL.**

**Goals:**
- Criar relatório customizado sem chamar suporte (construtor visual).
- Agendar envio automático pra diretoria ou cliente externo.
- Exportar pra Excel/CSV pra análise externa.
- Garantir que a métrica X tem a MESMA definição em todos os módulos (governança de definição).

**Frustrations:**
- Ferramenta de BI exige treinamento longo (Power BI / Tableau).
- "Métrica faturamento aqui é diferente do módulo Y" — falta governança.
- Não consegue filtrar por filial / equipe sem TI.
- Indicador que demora 1 dia pra atualizar (precisa near-real-time).

**Jornada típica:** abre construtor → escolhe métrica + filtros + agrupamento → visualiza prévia → ajusta → salva dashboard pessoal OU agenda envio semanal.

**Devices:** web desktop.
**Frequência:** semanal.
**Permissões:** RBAC `analista` — leitura ampla; sem dado financeiro sensível por padrão.
**Módulos onde aparece:** `dados/bi` (principal), futuramente `financeiro/relatorios-financeiros`, `operacao/capacity-planning-operacional`, qualquer módulo que exponha métrica agregável.

---

## P-MKT-01 — Visitante Anônimo

**Perfil:** pessoa que chega ao site/portal público do tenant pela primeira vez (busca Google, WhatsApp, indicação). Pode ser pessoa física ou comprador de empresa. **Não tem login.** Tempo de atenção curto (< 3 min até desistir).

**Goals:**
- Entender rapidamente o que a empresa oferece.
- Ver preço (ou faixa) sem precisar ligar.
- Pedir orçamento sem ter que cadastrar conta completa.
- Saber se a empresa atende a região dele.

**Frustrations:**
- Site que esconde preço atrás de "fale conosco".
- Formulário que pede CNPJ, CEP, fax e cargo só pra mostrar produto.
- Página lenta no mobile.

**Jornada típica:** chega pelo Google buscando "calibração balança em [cidade]" → vê vitrine com serviços + faixa de preço → adiciona "calibração balança 30kg" ao carrinho → preenche nome + telefone + e-mail + termo LGPD → recebe confirmação por WhatsApp. Depois vira lead e migra pra P-MKT-02 (cliente cadastrado).

**Devices:** mobile (60%) + desktop (40%).
**Frequência:** uma única visita até virar lead.
**Permissões:** público — sem login. Coleta de dado pessoal cobre apenas o estritamente necessário (LGPD minimização).
**Módulos onde aparece:** `comercial/marketplace` (vitrine pública), `comercial/portal-cliente` (landing pré-login), futuramente qualquer página pública gerada pelo tenant.

---

## Personas específicas (vão pro módulo ou domínio)

| Persona | Módulo / Domínio |
|---------|------------------|
| Técnico de campo | `dominios/operacao/personas.md` P-OP-01 |
| Signatário técnico | `dominios/metrologia/personas.md` P-METR-02 |
| Metrologista de bancada | `dominios/metrologia/personas.md` P-METR-01 |
| Vendedor com comissão | `dominios/comercial/personas.md` + `financeiro/comissoes` |
| Cliente final do tenant | `dominios/comercial/modulos/clientes/personas.md` |
| Suporte Aferê | `dominios/suporte-plataforma/modulos/suporte-saas/personas.md` |
| Gerente operacional (op. + SLA) | `dominios/operacao/personas.md` P-OP-04 (op.) + `dominios/comercial/modulos/sla-contratual/personas.md` Persona 3 (SLA) |

---

## Referências

- `docs/discovery/personas-detalhadas.md` (16 personas completas com goals/frustrations)
- `docs/discovery/jobs-to-be-done.md` (BIG-01..BIG-12)
- `docs/dominios/<dominio>/personas.md` (personas por domínio)
