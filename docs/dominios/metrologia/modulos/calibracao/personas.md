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

## P-METR-AUDITOR-CGCRE (Auditor externo CGCRE) — papel em Calibração

> Adicionado em 2026-05-23 (Onda 7D — ALTO-PEND-2 R2 produto). Persona externa não-usuária do produto, mas referenciada em US-CER-003 e em todo o fluxo de supervisão regulatória.

**Função:** profissional credenciado pelo CGCRE (Coordenação Geral de Acreditação do INMETRO) que conduz auditoria de manutenção/supervisão (a cada 12-24 meses) ou avaliação de acreditação inicial em laboratórios RBC. Trabalha como consultor terceirizado contratado pelo CGCRE.

**Goals em Calibração (consultivo, não tem login no Aferê):**
- Verificar evidência objetiva da conformidade com ISO/IEC 17025:2017 + NIT-DICLA-021.
- Auditar registros técnicos (cl. 7.5) e validar rasura digital (LeituraCorrecao).
- Confirmar 2ª conferência independente (cl. 6.2.5 + INV-CAL-CONF-001) e exceções dentro do limite 5%/mês.
- Validar cadeia de rastreabilidade metrológica (`PadraoUsado.snapshot_padrao` + cert do padrão vigente).
- Verificar fluxo CAPA completo (cl. 7.10 + 8.7 — `NaoConformidade` com causa-raiz + eficácia).
- Validar versionamento do motor de cálculo (cl. 7.11 — INV-CAL-VERSAO-001) e replay determinístico.

**O que o tenant apresenta ao auditor:**
- Lista de calibrações em período auditado.
- Para cada uma: registros técnicos imutáveis (Leitura, LeituraCorrecao, CondicoesAmbientais, OrcamentoIncerteza + filhas, RevisaoTecnica, EventoDeCalibracao WORM).
- Dossiês de validação de software (URS/IQ/OQ/PQ por release — ADR-0025).
- Política de exceção 6.2.5 + auditoria trimestral do gestor de qualidade.
- Cadeia metrológica de cada padrão usado.

**Devices:** notebook próprio do auditor; tenant exporta evidência em PDF + provas hash de imutabilidade WORM. Aferê **não** fornece acesso direto ao banco — auditor recebe via tenant.

**Próximo review:** quando 1º tenant Aferê for acreditado RBC (V2).

---

## P-METR-AUDITOR-INMETRO (Auditor INMETRO/IPEM) — papel em Calibração

> Adicionada em 2026-05-23. Aplica-se a verificações INMETRO (atividade `verificacao_inmetro` na ADR-0023) — fiscalização da Lei 9.933/99.

**Função:** profissional INMETRO ou IPEM estadual que verifica conformidade de instrumentos de medição de uso público obrigatório (balanças comerciais, bombas de combustível, etc.).

**Goals em Calibração:** consulta laudo de verificação INMETRO + cadeia de rastreabilidade do padrão usado. Não interage com calibração RBC tradicional, mas pode requisitar evidência se tenant atende ambos os escopos.

---

## Convenções

- RT é persona transversal Calibração + Certificados — quando consolidar, promover pra `../../personas.md` (domínio metrologia).
- Recepcionista pode ser transversal com Ordens de Serviço — verificar antes de promover.
- Auditores externos (CGCRE, INMETRO) são personas não-usuárias mas citadas em US/AC — devem ser declaradas pra rastreabilidade.
