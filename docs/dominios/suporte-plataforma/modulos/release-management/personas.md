---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas — Módulo Release Management

---

## Persona 1: Gerente de Produto Aferê (Release Owner)

**Identidade:** Roldão + futuros PMs. Decide o que vai em cada release.

**Goals deste módulo:**
- Liberar feature pra tenant certo no momento certo (flags + planos).
- Comunicar mudanças sem ruído.
- Evitar quebrar integração de cliente.

**Frustrations específicas:**
- Liberar feature pra todo mundo e quebrar tenant grande.
- Esquecer de avisar breaking change e gerar incidente.
- Flag esquecida no código por meses (débito técnico).

**Jornada típica:**
1. Define escopo da release.
2. Cria feature flags necessárias.
3. Marca tenants beta.
4. Publica release notes.
5. Acompanha métricas de adoção.
6. Cleanup de flags antigas.

**Devices:** web desktop.
**Frequência:** semanal a quinzenal.

---

## Persona 2: SRE / Operador do Aferê

**Identidade:** Equipe que mantém o sistema rodando.

**Goals deste módulo:**
- Migração de dados sem perda.
- Rollback rápido em caso de falha.
- Coordenar janela de manutenção com mínimo impacto.

**Frustrations específicas:**
- Migração que não tem rollback documentado.
- Release que precisa janela mas ninguém comunicou.

**Devices:** web desktop + terminal.
**Frequência:** por release.

---

## Persona 3: Tenant Admin (consumidor das releases)

**Identidade:** Dono ou TI do tenant.

**Goals deste módulo:**
- Saber o que mudou antes de virar dúvida da equipe dele.
- Optar pelo programa beta se quiser ver features novas antes.
- Ter ambiente de homologação se for Enterprise.

**Frustrations específicas:**
- Tela mudar do dia pra noite sem aviso.
- Integração quebrar sem antecedência.

**Devices:** web desktop.
**Frequência:** mensal.

---

## Persona 4: Integrador (consumidor da API)

**Identidade:** Dev parceiro / sistema externo do tenant.

**Goals deste módulo:**
- Saber de breaking changes com antecedência longa (60+ dias).
- Manter integração estável.

**Frustrations específicas:**
- Endpoint mudar sem aviso.
- Deprecation warning chegar 7 dias antes da quebra.

**Devices:** API + e-mail.
**Frequência:** eventual (mas reage rápido).

---

## Convenções

Persona específica = responsabilidade única deste módulo. Promoção pra `../../personas.md` se aparecer em ≥2.
