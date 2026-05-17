---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Licenças e Acreditações

> Personas específicas deste módulo. Transversais ficam em `../../personas.md` (domínio) e `docs/comum/personas.md` (produto).

---

## Persona 1: Responsável administrativo de conformidade

**Identidade:** Administrativo/financeiro da empresa prestadora, 30-55 anos, geralmente acumula a função de "guardião de documentos" sem formação jurídica. Não programa. Conhece os prazos por memória e planilha.

**Goals deste módulo:**
- Saber quais documentos vencem nos próximos 90 dias sem abrir planilha.
- Receber alerta antes de qualquer auditoria/multa.
- Provar pra auditoria externa que tudo está em dia sem perder uma tarde montando dossiê.

**Frustrations específicas:**
- Esquece data de renovação e descobre o vencimento na hora da auditoria.
- Tem que pedir cópia do PDF pra contadora toda vez que precisa.
- Não sabe quais operações ficam bloqueadas se documento X vencer.

**Jornada típica:**
1. Recebe alerta de vencimento em 60 dias por e-mail.
2. Abre o módulo, vê documento, baixa cópia atual, inicia processo renovação.
3. Quando documento novo chega, cria nova revisão no sistema com anexo.
4. Alertas se reprogramam pela nova data.

**Devices:** web desktop principal; e-mail no mobile.
**Frequência:** semanal (consulta dashboard); diária quando há alerta ativo.

---

## Persona 2: Auditor externo (CGCRE, fisco, ANVISA)

**Identidade:** Auditor de órgão regulador ou auditor contratado pelo cliente final, 35-65 anos, exige evidência documental imutável e rastreável.

**Goals deste módulo:**
- Receber relatório consolidado em PDF assinado.
- Verificar hash do relatório contra trilha WORM.
- Ver histórico de renovações sem buracos.

**Frustrations específicas:**
- Empresa entrega documentos soltos, fora de ordem, sem comprovação de continuidade.
- Não consegue confirmar autenticidade do PDF.

**Jornada típica:**
1. Solicita relatório de licenças vigentes ao admin da empresa.
2. Recebe PDF + hash SHA-256.
3. Verifica hash + lê trilha imutável (acesso de leitura ao auditor).

**Devices:** web (acesso temporário via portal auditor).
**Frequência:** anual (CGCRE) ou ad-hoc.

---

## Persona 3: Responsável técnico (RT) — visão deste módulo

**Identidade:** Metrologista, engenheiro ou técnico habilitado, dono da ART/RRT vinculada à empresa. Detalhe completo no módulo Responsável Técnico (`../responsavel-tecnico/personas.md`); aqui interage apenas com a própria ART/RRT.

**Goals deste módulo:**
- Cadastrar ART/RRT e receber alerta de vencimento da própria habilitação.
- Não emitir certificado se ART vencida (proteção legal pessoal).

**Devices:** web + mobile.
**Frequência:** mensal (consulta status).

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Auditor externo aparece em vários módulos com sotaque distinto — quando responsabilidade for transversal, promover pra `docs/comum/personas.md`.
- RT é persona promovida ao domínio quando módulo Responsável Técnico existir.
