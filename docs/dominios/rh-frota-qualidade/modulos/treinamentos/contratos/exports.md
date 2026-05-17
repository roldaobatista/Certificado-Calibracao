---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: treinamentos
relacionados:
  - docs/conformidade/comum/retencao-matriz.md
---

# Contratos de Export — Módulo Treinamentos e Certificações Internas

> Formatos de saída. Inclui Certificado de Conclusão (prova de competência ISO 17025 cl. 6.2).

---

## Exports

### Export 1: Certificado de Conclusão (PDF)
**Propósito:** documento que comprova conclusão de treinamento e validade da capacitação — evidência objetiva para ISO/IEC 17025 cl. 6.2 e ISO 9001 cap. 7.2.
**Formato:** PDF.
**Regulado?:** sim — ISO 17025 cl. 6.2 (competência); formato livre, conteúdo mínimo regulado por boa prática.
**Validador externo:** auditor CGCRE / ISO inspeciona em supervisão (sem validador automatizado).
**Template:** template tenant configurável (logo, razão social, CNPJ).
**Campos obrigatórios:** identificação tenant (razão social + CNPJ), identificação colaborador (nome + CPF), nome do treinamento + sub-categoria, carga horária, data realização, validade, facilitador (nome + identificação), local, hash documento, QR code para verificação online no portal do tenant.
**Assinatura digital:** opcional V1 (touch + hash); ICP-Brasil em V2 (`INV-017`).
**Imutabilidade pós-emissão:** sim — `INV-001`.
**Retenção:** ≥10 anos (cobertura ISO 17025 cl. 8.4 e prescrição trabalhista). Ver `retencao-matriz.md`.

**Exemplo (snippet):**
```
[Logo tenant]
CERTIFICADO DE CONCLUSAO

[Nome colaborador], CPF ***.***.***-XX
concluiu com aproveitamento o treinamento
[Nome treinamento — sub-categoria]
Carga horária: 8h | Data: 01/06/2026 | Validade: 01/06/2028
Facilitador: [Nome] | Local: [Local]
Hash: sha256:abc123...
QR Code: [imagem]
```

---

### Export 2: Matriz de Competência (PDF + XLSX)
**Propósito:** evidência consolidada para auditoria ISO 17025 cl. 6.2 / ISO 9001.
**Formato:** PDF (legível) + XLSX (manipulável).
**Regulado?:** boa prática auditoria.
**Campos:** cabeçalho tenant, linhas (colaboradores ativos), colunas (habilidades), célula (status + validade), filtros aplicados, data emissão, hash.
**Assinatura digital:** opcional.
**Imutabilidade:** snapshot do momento da emissão.

---

### Export 3: Histórico de Capacitação do Colaborador (PDF — "Currículo Interno")
**Propósito:** consolidado vitalício do colaborador no tenant.
**Formato:** PDF.
**Regulado?:** boa prática.
**Campos:** dados colaborador, linha do tempo (eventos + certificados + validades), status atual.
**LGPD:** acesso por RBAC; colaborador pode requisitar próprio.

---

### Export 4: Lista de Presença do Evento (PDF)
**Propósito:** documentação interna da execução do evento.
**Formato:** PDF.
**Regulado?:** boa prática.
**Campos:** treinamento, data, local, facilitador, lista participantes com presença % + nota + assinatura digital.
**Imutabilidade:** após conclusão do evento.

---

### Export 5: Relatório de Bypass (PDF + XLSX)
**Propósito:** trilha de exceções aprovadas no período — para auditoria interna e governança.
**Formato:** PDF + XLSX.
**Regulado?:** uso interno + auditor pode solicitar.
**Campos:** período, lista bypass (colaborador, escopo, justificativa, aprovador, data, validade, status), totais por aprovador.
**Imutabilidade:** snapshot do período.

---

### Export 6: Pacote de Evidência ISO 17025 cl. 6.2 (ZIP)
**Propósito:** pacote pronto para supervisão CGCRE — Matriz + Certificados ativos dos signatários + Histórico dos técnicos.
**Formato:** ZIP contendo PDFs.
**Regulado?:** sim — formato livre, conteúdo cobre cl. 6.2.
**Campos:** ver itens individuais 1, 2, 3.
**Imutabilidade:** snapshot datado.

---

## Exports inter-módulos

- **Certificado de Conclusão (NR-*)** → consumido por `seguranca-trabalho/` para criar `TreinamentoSegurancaAplicado`.
- **Matriz de Competência** → referenciada por `qualidade/` em auditorias internas.
- **Pacote Evidência ISO 17025 cl. 6.2** → consumido pelo módulo `conformidade/iso-17025/` (a criar).

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Mudança de template do certificado → bump versão + janela coexistente 6 meses.
- ISO 17025 publica nova versão → ADR + revisão do conteúdo mínimo.

## Como esta lista evolui

- Export novo → adicionar + validar conteúdo mínimo regulado se aplicável.
