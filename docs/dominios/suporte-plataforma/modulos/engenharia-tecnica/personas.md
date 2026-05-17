---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Engenharia Técnica

> Personas específicas deste módulo. Transversais ficam em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Engenheiro Projetista

**Identidade:** engenheiro eletricista, mecânico ou de automação; CREA ativo; 25-50 anos; usa AutoCAD/Eplan/KiCad em paralelo.

**Goals deste módulo:**
- Subir desenho/diagrama/cálculo com metadados sem fricção.
- Reutilizar componentes da biblioteca sem cadastrar duplicados.
- Gerar memorial descritivo estruturado para entregar ao cliente.

**Frustrations:**
- Pasta de rede sem versionamento; perde rastreabilidade.
- Cliente pede "qual revisão foi instalada" e ninguém sabe.
- Cadastra mesmo componente 5 vezes com nomes diferentes.

**Jornada típica:**
1. Termina desenho no AutoCAD → exporta DWG + PDF.
2. Abre módulo, escolhe projeto, faz upload da revisão "B".
3. Atualiza BOM (item novo adicionado, quantidade alterada).
4. Marca motivo da revisão ("cliente pediu mudança de capacidade").
5. Submete pra aprovação técnica.

**Devices:** web desktop (upload + edição metadados); raramente mobile.
**Frequência:** diário-semanal.

---

## Persona 2: Engenheiro Responsável Técnico (aprovador)

**Identidade:** engenheiro sênior, CREA com responsabilidade técnica pela empresa-tenant; aprova projetos formalmente; pode assinar com certificado digital.

**Goals:**
- Ver pendências de aprovação técnica em painel.
- Comparar revisão B vs A (diff) antes de aprovar.
- Assinatura registrada com nome/CREA/data/IP — defesa em caso de litígio.

**Frustrations:**
- Aprovação por email sem registro formal.
- Revisar projeto sem ver o que mudou.
- Assinatura digital fora do fluxo (PDF separado).

**Jornada típica:**
1. Recebe notificação de pendência.
2. Abre painel BPM (pendências) ou painel do módulo Engenharia.
3. Abre diff revisão B vs A.
4. Aprova (assinatura registrada) ou rejeita com comentário.

**Devices:** web desktop.
**Frequência:** semanal.

---

## Persona 3: Técnico de Campo (consumidor)

**Identidade:** técnico que vai a campo montar/manutenir equipamento; pode ter formação técnica em mecânica/eletrônica; usa mobile.

**Goals deste módulo:**
- Ver revisão aprovada mais recente do projeto técnico vinculado à OS.
- Baixar PDF/imagem do desenho para consulta offline.
- Receber alerta se há revisão nova ainda em rascunho (não atuar com versão velha sem saber).

**Frustrations:**
- Chegar em campo com desenho desatualizado.
- Não ter sinal de internet pra consultar.

**Jornada típica:**
1. Abre OS no mobile.
2. Vê link "Projeto Técnico Rev. B (aprovada)".
3. Baixa PDF antes de sair do escritório (offline-first).
4. Executa em campo consultando o PDF baixado.

**Devices:** mobile (Flutter, offline-first — ADR-0009).
**Frequência:** diário.

---

## Persona 4: Auditor (interno ou cliente)

**Identidade:** pessoa que precisa rastrear conformidade — pode ser cliente final, fiscal de obra, auditor interno do tenant.

**Goals:**
- Consultar histórico completo de revisões.
- Ver quem aprovou cada revisão.
- Saber qual revisão estava ativa no momento de uma OS específica.

**Devices:** web desktop.
**Frequência:** eventual.

---

## Convenções

- "Engenheiro Projetista" e "Engenheiro Responsável" são papéis com responsabilidades distintas — não promover pra domínio sem evidência de uso em outros módulos.
- "Técnico de Campo" pode aparecer em vários módulos; se virar transversal, promover pra `../../personas.md`.
