---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
---

# Personas — Módulo Segurança do Trabalho

> Personas específicas deste módulo. Transversais em `../../personas.md`.

---

## Persona 1: Gerente / Técnico SST

**Identidade:** Profissional responsável por Segurança do Trabalho do tenant (pode ser Técnico de Segurança formado, Engenheiro de Segurança, ou gerente operacional acumulando função em empresa pequena). Geralmente 30-55 anos. Em laboratório metrológico pequeno costuma ser o próprio dono ou o gerente operacional.

**Goals deste módulo:**
- Manter 100% da equipe com EPI, ASO e treinamento de segurança válidos.
- Reduzir taxa de acidentes / quase-acidentes.
- Ter trilha documental defendível em fiscalização MTE / ação trabalhista.
- Emitir Permissão de Trabalho e validar APR para serviços de risco.

**Frustrations específicas:**
- Planilha de controle de EPI desatualizada; descobre EPI vencido só quando alguém se machuca.
- Termo de entrega de EPI em papel — perde-se e não vale em juízo.
- Técnico em campo executando OS sem checklist porque "estava com pressa".
- Treinamento vencido descoberto na hora da emergência.

**Jornada típica:**
1. Manhã: abre painel de alertas SST (EPIs / ASOs / treinamentos a vencer).
2. Antes de cada OS de risco: valida PT + APR.
3. Quando ocorre acidente / quase-acidente: registra no sistema com fotos + ação corretiva.
4. Mensal: emite relatório de segurança para gerência.

**Devices:** web desktop (escritório); mobile (em campo / SIPAT).
**Frequência:** diário.

---

## Persona 2: Técnico de campo (executante)

**Identidade:** Técnico de assistência técnica / calibração que executa OS no cliente. 25-50 anos. Vê SST como burocracia mas entende que protege o emprego dele.

**Goals deste módulo:**
- Receber EPI e treinamento sem complicação.
- Preencher checklist rápido (≤2 min) antes de iniciar OS.
- Registrar quase-acidente sem medo de retaliação.

**Frustrations específicas:**
- Checklist longo / repetitivo desestimula uso.
- Termo de EPI em papel exige passar no escritório só pra assinar.

**Jornada típica:**
1. Recebe EPI; assina termo no celular (touch).
2. Em campo: abre OS no app, marca checklist de segurança, anexa foto se necessário.
3. Se quase-acidente: registra com foto + descrição.

**Devices:** mobile.
**Frequência:** diário.

---

## Persona 3: Auditor MTE / fiscal trabalhista

**Identidade:** Auditor externo (Auditor-Fiscal do Trabalho) que pode aparecer no tenant. Não usa o sistema direto; recebe relatórios.

**Goals deste módulo:**
- Validar que tenant tem trilha documental de EPI entregue + ASO + treinamento de segurança.
- Validar registro de acidentes.

**Frustrations específicas:**
- Tenant que apresenta documento sem assinatura / sem data / "perdeu o original".

**Devices:** consome relatório PDF.
**Frequência:** evento raro.

---

## Convenções

- Persona específica = papel com responsabilidade única neste módulo.
- Promover pra `../../personas.md` se aparece em ≥2 módulos.
