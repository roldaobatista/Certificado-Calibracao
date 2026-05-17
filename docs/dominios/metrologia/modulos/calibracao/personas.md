---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
---

# Personas do módulo Calibração

> Personas específicas. Transversais ficam em `../../personas.md` (domínio) + `docs/comum/personas.md`.
>
> **Promovidas em 2026-05-17 pro domínio metrologia (`../../personas.md`):** Metrologista executor (P-METR-01) + Responsável Técnico signatário (P-METR-02). As entradas abaixo (Persona 1 e Persona 2) permanecem como **detalhamento específico da execução de calibração** — visão canônica vive no domínio.

---

## Persona 1: Metrologista executor

> **Canônica:** `../../personas.md` P-METR-01. Abaixo, o recorte do que esta persona faz **especificamente** durante a execução da calibração.

**Identidade:** Técnico/tecnólogo metrologia ou física, 25-50 anos, formação técnica média/superior, opera o instrumento padrão, faz as leituras, alimenta o sistema. Pode ou não ser signatário (geralmente é o de menor senioridade).

**Goals deste módulo:**
- Executar calibração em fluxo claro sem ter que abrir Excel paralelo.
- Saber rápido se padrão está vigente, se faixa está no escopo.
- Não digitar leitura duas vezes (integração com balança/padrão quando possível).

**Frustrations específicas:**
- Sistema atual obriga sair pro Excel pra calcular incerteza.
- Não há trava — emite cert com padrão vencido e descobre na auditoria.

**Jornada típica:**
1. Recebe instrumento na bancada.
2. Configura calibração (grandeza, faixa, pontos).
3. Seleciona padrões.
4. Registra leituras (manual ou integrado).
5. Sistema calcula erro + incerteza.
6. Encaminha pra revisão técnica.

**Devices:** desktop laboratório principal; tablet/mobile auxiliar.
**Frequência:** diária.

---

## Persona 2: Responsável Técnico signatário (RT)

> **Canônica:** `../../personas.md` P-METR-02. Abaixo, o recorte do que o RT faz **especificamente** na revisão de calibração.

**Identidade:** Metrologista sênior, formação técnica/superior, registro CRQ/CREA quando aplicável, dono do A3, autorizado pela CGCRE como signatário no escopo do laboratório.

**Goals deste módulo:**
- Revisar calibração rapidamente, com tudo em uma tela.
- Fazer 2ª conferência sem ter que reabrir Excel.
- Não assinar nada fora do escopo de acreditação.

**Frustrations específicas:**
- Hoje revisa em planilha + sistema separado.
- Aprova cert e descobre depois que padrão estava vencido.

**Jornada típica:**
1. Abre fila de revisão (calibrações pendentes).
2. Revisa: checa padrões, condições ambientais, orçamento de incerteza, decisão.
3. Aprova / pede correção / rejeita.
4. Faz 2ª conferência (idealmente em outra calibração feita por colega).
5. Após 2ª, dispara emissão de certificado (módulo Certificados).

**Devices:** desktop.
**Frequência:** diária.

---

## Persona 3: Recepcionista do laboratório

**Identidade:** Administrativo do lab, 20-50 anos, registra entrada/saída de instrumentos, gera etiquetas, atende cliente.

**Goals deste módulo:**
- Registrar entrada em < 2 min.
- Gerar etiqueta interna com QR Code automático.

**Devices:** desktop recepção + impressora térmica/laser.
**Frequência:** diária.

---

## Persona 4: Gestor da qualidade (ISO 17025)

**Identidade:** Responsável pelo sistema de gestão da qualidade do lab, geralmente RT sênior ou perfil específico. Cobra evidências, audita registros, planeja participação em proficiência.

**Goals deste módulo:**
- Ver indicadores: taxa de rejeição, tempo médio, escore proficiência.
- Programar verificações intermediárias dos padrões.
- Registrar comparações interlaboratoriais.

**Devices:** desktop.
**Frequência:** semanal/mensal.

---

## Convenções

- RT é persona transversal Calibração + Certificados — quando consolidar, promover pra `../../personas.md` (domínio metrologia).
- Recepcionista pode ser transversal com Ordens de Serviço — verificar antes de promover.
