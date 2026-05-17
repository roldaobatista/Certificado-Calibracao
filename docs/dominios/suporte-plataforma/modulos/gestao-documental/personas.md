---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas — Módulo Gestão Documental

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Responsável Documental do Tenant

**Identidade:** Gestor administrativo ou de qualidade, 30-50 anos, formação técnica ou administrativa. Cuida do acervo da empresa.

**Goals deste módulo:**
- Centralizar todos os documentos em um único lugar versionado.
- Garantir que documentos vencendo sejam renovados a tempo.
- Saber quem acessou cada documento sensível.

**Frustrations específicas:**
- Documento crítico perdido em pasta de Drive de ex-funcionário.
- Versões duplicadas circulando (v_final, v_final_FINAL, v_definitivo).
- Validade venceu e ninguém percebeu — perdeu contrato.

**Jornada típica:**
1. Faz upload de documento e vincula à entidade certa.
2. Define vigência + responsável pela renovação.
3. Recebe notificação 30 dias antes do vencimento.
4. Substitui versão e mantém histórico auditável.

**Devices:** web desktop primário; mobile pra consulta.
**Frequência:** diário.

---

## Persona 2: Auditor / Compliance Officer

**Identidade:** Auditor interno ou consultor externo (ISO 9001, ISO 17025, LGPD).

**Goals deste módulo:**
- Provar que documento estava vigente em data específica.
- Provar que apenas pessoas autorizadas acessaram doc sensível.
- Verificar política de retenção sendo cumprida.

**Frustrations específicas:**
- Não conseguir reconstruir histórico de versões.
- Trilha de auditoria com lacunas.

**Jornada típica:**
1. Pede "todos os acessos ao contrato X entre data Y e Z".
2. Pede "qual versão do procedimento estava vigente em data W".
3. Exporta trilha pra evidência de auditoria.

**Devices:** web desktop.
**Frequência:** mensal a anual.

---

## Persona 3: Usuário Operacional

**Identidade:** Atendente, técnico, vendedor — usa documentos no dia a dia mas não gerencia.

**Goals deste módulo:**
- Buscar documento rápido pelo conteúdo.
- Anexar foto/PDF a OS / cliente.
- Compartilhar documento com cliente externo.

**Frustrations específicas:**
- Não achar documento que sabe que existe.
- Tela complicada com muitos campos.

**Devices:** web + mobile.
**Frequência:** diário.

---

## Convenções

Persona específica = responsabilidade única deste módulo. Se aparecer em ≥2 módulos, promover.
