---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/dominios/dados/personas.md
  - docs/comum/personas.md
---

# Personas do módulo BI

> Personas **específicas** do módulo BI. Transversais ficam em `../../personas.md` (domínio) e `docs/comum/personas.md`.

---

## Persona 1: Analista de indicadores / responsável por relatórios

**Identidade:** Pode ser o próprio dono em empresa pequena, ou perfil dedicado em empresa maior. Familiaridade média com planilhas (Excel). Não programa SQL. 25-50 anos.

**Goals deste módulo:**
- Criar relatório customizado sem chamar suporte.
- Agendar envio automático.
- Exportar para Excel/CSV.

**Frustrations específicas:**
- Ferramenta de BI exigir treinamento longo.
- Não conseguir filtrar por filial sem TI.
- "Métrica X aqui diferente do módulo Y" (falta de governança de definições).

**Jornada típica:**
1. Abre construtor → escolhe métrica + filtros + agrupamento.
2. Visualiza prévia → ajusta.
3. Salva dashboard pessoal OU agenda envio.

**Devices:** web desktop.
**Frequência:** semanal.

**Permissões:** RBAC `analista` — leitura ampla; sem dado financeiro sensível por padrão.

---

## Persona 2: Cliente externo consumidor de dashboard público (Wave B+)

**Identidade:** Cliente do tenant que recebeu link público (ex: empresa grande monitorando SLA dos serviços contratados).

**Goals:**
- Ver indicadores próprios sem precisar criar login.

**Frustrations:**
- Login chato — prefere link.
- Indicador desatualizado.

**Jornada típica:**
1. Recebe link por e-mail.
2. (Opcional) digita senha.
3. Vê dashboard restrito ao seu próprio relacionamento.

**Notas de risco:**
- Link público é **superfície LGPD**. Toda info exposta passa por agregação OU pertence exclusivamente ao próprio cliente.
- `INV-TENANT-*` valida que dashboard externo nunca vaza outro tenant.

**Devices:** mobile + desktop.
**Frequência:** ocasional.

---

## Persona 3: Dono executivo (P1 reutilizada — comportamento específico aqui)

Ver `docs/comum/personas.md` P1. No BI:
- Consome **resumo** (não constrói relatório).
- Quer mobile (consulta em movimento) + e-mail agendado (não precisa abrir o app).

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Se persona aparece em ≥2 módulos com mesma responsabilidade → promover pra `../../personas.md` (domínio).
- Se aparece em ≥2 domínios → promover pra `docs/comum/personas.md`.
