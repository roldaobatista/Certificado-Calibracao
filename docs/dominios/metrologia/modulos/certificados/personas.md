---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Certificados

> Personas específicas. Transversais ficam em `../../personas.md` (domínio) + `docs/comum/personas.md`.

---

## Persona 1: Responsável Técnico (RT) — visão emissão

**Identidade:** Metrologista signatário autorizado, formação técnica metrologia/física/engenharia, registro CRQ/CREA, dono do A3 vinculado à empresa. Detalhe full em `../calibracao/personas.md`; aqui interage como signatário.

**Goals deste módulo:**
- Assinar lote de certificados sem atrito (token A3 detectado uma vez, assinatura em segundos).
- Reemitir certificado quando descobre erro, mantendo trilha auditável.
- Não emitir certificado RBC quando acreditação CGCRE vencida (proteção legal).

**Frustrations específicas:**
- Tela trava no momento da assinatura, perde 5 min.
- Sistema permite emitir sem revisar — risco de erro factual sair pro cliente.

**Jornada típica:**
1. Calibração revisada chega na fila de emissão.
2. RT abre certificado, confere dados, clica "assinar".
3. Web PKI Lacuna abre prompt do token, RT digita PIN.
4. Sistema marca ASSINADO + dispara e-mail cliente.

**Devices:** web desktop principal (token A3 USB); mobile só consulta.
**Frequência:** diária.

---

## Persona 2: Cliente final do laboratório

**Identidade:** Empresa cliente que tem instrumentos calibrados. Pessoa que consulta no portal é geralmente o engenheiro/qualidade do cliente. 25-55 anos. Não precisa entender metrologia profunda — quer comprovação documental.

**Goals deste módulo:**
- Baixar certificado pelo portal sem ter que pedir por e-mail.
- Verificar autenticidade do certificado (QR Code → página pública).
- Ver todos os certificados dos seus instrumentos em um lugar.

**Frustrations específicas:**
- Recebe certificado em PDF anexo + se perde no e-mail meses depois.
- Auditor cliente questiona autenticidade e ele não sabe provar.

**Jornada típica:**
1. Recebe e-mail "seu certificado está disponível".
2. Acessa portal, baixa PDF, salva na pasta de qualidade.
3. Eventualmente escaneia QR Code da etiqueta na auditoria.

**Devices:** web (desktop e mobile).
**Frequência:** mensal/trimestral.

---

## Persona 3: Auditor CGCRE / cliente do cliente

**Identidade:** Auditor de órgão regulador ou auditor 3rd party contratado pelo cliente final do laboratório. Verifica autenticidade de certificados na auditoria.

**Goals deste módulo:**
- Escanear QR Code do certificado e ver autenticidade + versão atual + se foi substituído/cancelado.
- Conferir numeração sequencial e ausência de gaps.

**Frustrations específicas:**
- Certificado em PDF sem verificação online — não há como saber se foi adulterado.

**Jornada típica:**
1. Encontra etiqueta no instrumento → escaneia QR.
2. Página pública abre com status (vigente/expirado/cancelado/substituído).
3. Marca conformidade na auditoria.

**Devices:** mobile (câmera do celular pra QR).
**Frequência:** anual ou pontual.

---

## Persona 4: Admin tenant — gestor de templates

**Identidade:** Administrador da conta no SaaS. Geralmente sócio ou gestor da qualidade. Customiza visual dos documentos pra identidade da empresa.

**Goals deste módulo:**
- Subir logo + ajustar cabeçalho/rodapé/cores sem mexer em código.
- Versionar template — manter histórico.

**Devices:** web desktop.
**Frequência:** raro (set up + ajustes ocasionais).

---

## Convenções

- RT é persona transversal Calibração + Certificados — promovida pra `../../personas.md` (domínio).
- Cliente final + Auditor são transversais ao produto — promover pra `docs/comum/personas.md` quando consolidar.
