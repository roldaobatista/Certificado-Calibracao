---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/personas.md
  - docs/dominios/metrologia/modulos/calibracao/personas.md
  - docs/dominios/metrologia/modulos/certificados/personas.md
---

# Personas do domínio Metrologia

> Personas que aparecem em **≥2 módulos do domínio Metrologia** (calibração + certificados + licenças-acreditações). Personas que aparecem em ≥2 domínios ficam em `docs/comum/personas.md`. Personas exclusivas de um módulo ficam em `modulos/<modulo>/personas.md`.

---

## P-METR-01 — Metrologista de bancada

**Quem é:** 25-55 anos. Técnico/tecnólogo metrologia, física ou engenharia. Formação técnica média/superior. Trabalha no laboratório fixo da empresa: recebe instrumento, executa calibração, alimenta o sistema. Pode ou não ser signatário (geralmente é o de menor senioridade — o sênior assina).

**Goals (transversais aos módulos do domínio):**
- Executar calibração em fluxo claro sem ter que abrir Excel paralelo.
- Saber rápido se padrão está vigente e se faixa está no escopo de acreditação.
- Não digitar leitura duas vezes (integração com balança/padrão MODBUS/OPC-UA quando possível).
- Receber instrumento + identificar por QR Code + abrir OS em < 2 min.
- Encerrar OS gerando certificado sem retrabalho — sem precisar passar pelo Excel pra calcular incerteza.
- Saber se há NC pendente que bloqueia emissão.

**Frustrations:**
- "Tenho que digitar tudo no Cali e depois no Excel."
- Pesos padrão sem rastreabilidade de uso histórico.
- Certificado emitido com erro → revisão manual + email pro cliente.
- Não há trava — emite cert com padrão vencido e descobre na auditoria.

**Jornada típica:**
1. Recebe instrumento na bancada → identifica QR Code → abre OS.
2. Configura calibração (grandeza, faixa, pontos).
3. Seleciona padrões da lista (sistema valida vigência + escopo).
4. Registra leituras (manual ou integrado).
5. Sistema calcula erro + incerteza automaticamente.
6. Encaminha pra revisão técnica (signatário).

**Devices:** desktop laboratório principal + tablet/mobile auxiliar.
**Conhecimento:** alto em metrologia, médio em informática. Usa o sistema diariamente.
**Frequência:** diária.
**Permissões:** RBAC `metrologista` — OS de calibração (criar / executar / encerrar) + escolher padrão + encaminhar pra revisão. **Não emite certificado** salvo se for também signatário com competência válida.

**Módulos onde aparece:** `metrologia/calibracao` (principal — executa), `metrologia/certificados` (encaminha pra emissão), `metrologia/licencas-acreditacoes` (consome escopo + vigência do padrão), `operacao/os` (a OS é o contêiner do trabalho).

**Origem:** P-OP-02 (`docs/dominios/operacao/personas.md`) era equivalente; a partir de 2026-05-17 a fonte canônica é esta entrada do domínio metrologia. O verbete em `operacao/personas.md` permanece como referência cruzada.

---

## P-METR-02 — Signatário técnico / Responsável Técnico (RT)

**Quem é:** 35-60 anos. Metrologista sênior, formação técnica/superior, registro CRQ/CREA quando aplicável, dono do certificado A3 (ICP-Brasil) vinculado à empresa. Autorizado pela CGCRE como signatário em escopo específico da acreditação RBC. **Pessoa física legalmente responsável** pelo conteúdo técnico de cada certificado que assina.

**Goals (transversais):**
- Revisar calibração rapidamente, com tudo em uma tela (padrões, condições ambientais, orçamento de incerteza, decisão).
- Fazer 2ª conferência sem ter que reabrir Excel.
- Assinar lote de certificados sem atrito (token A3 detectado uma vez, assinatura em segundos).
- **Não** assinar nada fora do escopo de acreditação — sistema bloqueia (INV-003).
- Reemitir certificado quando descobre erro, mantendo trilha auditável.
- **Não** emitir certificado RBC quando acreditação CGCRE vencida (proteção legal).

**Frustrations:**
- Hoje revisa em planilha + sistema separado.
- Aprova cert e descobre depois que padrão estava vencido.
- Tela trava no momento da assinatura, perde 5 min.
- Sistema permite emitir sem revisar — risco de erro factual sair pro cliente.

**Jornada típica:**
1. Abre fila de revisão (calibrações pendentes).
2. Revisa: confere padrões, condições, incerteza, decisão.
3. Aprova / pede correção / rejeita.
4. (Idealmente) faz 2ª conferência em calibração feita por colega.
5. Dispara emissão de certificado.
6. Web PKI Lacuna abre prompt do token → digita PIN → certificado ASSINADO + e-mail cliente.

**Devices:** web desktop principal (token A3 USB). Mobile só consulta.
**Conhecimento:** alto em metrologia + alto em ISO 17025. Médio em informática.
**Frequência:** diária.
**Permissões:** RBAC `signatario` — revisar + aprovar + assinar dentro do escopo declarado. Sistema valida: (a) competência válida (curso + assinatura CGCRE), (b) escopo de assinatura cobre a grandeza/faixa, (c) A3 vinculado ativo, (d) acreditação do laboratório vigente.

**Módulos onde aparece:** `metrologia/calibracao` (revisa), `metrologia/certificados` (assina), `metrologia/licencas-acreditacoes` (consome competência declarada + vigência).

**Compliance:** INV-003 (signatário só assina no escopo); cl. 6.2 da ISO 17025; NIT-DICLA-021.

---

## Convenções

- **Promoção:** persona que aparece em ≥2 módulos do domínio metrologia → vem pra cá. Em ≥2 domínios → vai pra `docs/comum/personas.md`.
- **Não duplicar:** módulos referenciam estas entradas em vez de redefinir.
- **Personas específicas** (recepcionista do lab, gestor de templates, gestor da qualidade ISO 17025) permanecem nos respectivos `modulos/<modulo>/personas.md`.

## Referências

- `docs/comum/personas.md` — transversais ao produto.
- `docs/dominios/metrologia/modulos/calibracao/personas.md` — Personas 1, 2 detalham execução por módulo.
- `docs/dominios/metrologia/modulos/certificados/personas.md` — Persona 1 detalha emissão por módulo.
- `docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md` — regras de competência do signatário.
- `docs/discovery/personas-detalhadas.md` (Persona 7 metrologista; Persona 12 RT).
