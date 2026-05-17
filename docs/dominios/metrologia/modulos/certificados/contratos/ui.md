---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Certificados

> Telas do módulo. Descritivo enquanto stack não cravada (ADR-0001).

---

## Telas

### Tela 1: Fila de Emissão

**Propósito:** RT vê calibrações prontas pra virar certificado.
**Persona principal:** Responsável Técnico.
**US:** `US-CER-001`.

**Elementos:**
- Filtros: tipo, cliente, faixa de data, prioridade.
- Tabela: OS, cliente, instrumento, calibração concluída em, RT que revisou, ação "gerar certificado".
- Indicador de bloqueio: se acreditação CGCRE vencida, badge vermelho "emissão RBC bloqueada".

**Estados:** padrão.
**Acessibilidade:** AA.
**Mobile:** consulta sim, emissão preferencial desktop (token A3).

---

### Tela 2: Detalhe/Pré-visualização do Certificado

**Propósito:** RT confere dados antes de assinar.
**Persona principal:** RT.
**US:** `US-CER-001`, `US-CER-002`.

**Elementos:**
- Cabeçalho: tipo, número (reservado), versão, status.
- Pré-visualização PDF (iframe).
- Painel lateral: snapshot dos dados (cliente, instrumento, padrões, leituras, incerteza, decisão).
- Botões: "Editar antes de assinar" (só em RASCUNHO), "Assinar com A3", "Cancelar".
- Aviso visual de bloqueios (acreditação, ART/RRT).

**Estados:**
- A3 não detectado: instrução "conecte o token A3 e atualize".
- Assinando: spinner com etapas (gerando hash → enviando ao Lacuna → recebendo PKCS#7 → anexando ao PDF).
- Sucesso: badge "ASSINADO" + redireciona pra Detalhe.

**Acessibilidade:** AA.
**Mobile:** consulta apenas; assinatura no desktop.

---

### Tela 3: Detalhe de Certificado Emitido

**Propósito:** consulta + ações pós-emissão.
**Persona principal:** RT + admin + cliente (visão filtrada).

**Elementos:**
- Cabeçalho status + número + versão + link "versão anterior" se aplicável.
- Abas: PDF | Snapshot dados | Assinatura | Envios | Etiquetas | Verificações públicas | Histórico de versões.
- Aba Assinatura: signer, CPF/CNPJ, signing time, thumbprint, validar agora (verifica cadeia ICP).
- Aba Envios: lista tentativas, status, retry manual.
- Aba Verificações: log de acessos à página pública.
- Ações: Reemitir | Cancelar | Imprimir etiqueta | Reenviar e-mail.

**Estados:** padrão.
**Acessibilidade:** AA.

---

### Tela 4: Reemissão

**Propósito:** criar nova versão linkada.
**US:** `US-CER-004`.

**Elementos:**
- Resumo da versão atual.
- Form: motivo (textarea ≥ 50 chars), o que mudou (campos editáveis: cliente, instrumento, padrões, leituras — herda do anterior, RT ajusta).
- Aviso visual: "ao salvar, esta nova versão substitui a atual; ambas ficam visíveis."
- Botão "Gerar nova versão" → vai pra fluxo de assinatura.

---

### Tela 5: Editor de Templates

**Propósito:** admin customiza visual.
**US:** `US-CER-010`.

**Elementos:**
- Lista de templates por tipo, com versão ativa marcada.
- Editor: upload logo, picker de cor primária, editor de cabeçalho/rodapé (rich text limitado — sem JS), variáveis dinâmicas disponíveis.
- Pré-visualização ao vivo com dados fictícios.
- Botões: salvar como nova versão | ativar.

---

### Tela 6: Portal do Cliente — Lista de Certificados

**Propósito:** cliente vê seus certificados.
**Persona:** cliente final.
**US:** `US-CER-006`.

**Elementos:**
- Filtros: instrumento, período, status (vigente/expirado).
- Tabela: número, tipo, instrumento, data emissão, validade recomendada, status, download.
- Aviso se versão substituída: link pra atual.

**Estados:** padrão.
**Acessibilidade:** AA.
**Mobile:** responsivo prioritário.

---

### Tela 7: Página Pública Verificadora (QR Code)

**Propósito:** auditor escaneia QR e vê status.
**Persona:** auditor/cliente do cliente.
**US:** `US-CER-009`.
**Acesso:** sem login, URL `/v/{qr_token}`.

**Elementos:**
- Cabeçalho neutro (sem branding do tenant explícito — mínimo necessário LGPD).
- Status grande: VIGENTE | EXPIRADO | CANCELADO | SUBSTITUIDA POR v(N+1).
- Número certificado + tipo + data emissão + validade recomendada.
- Razão social emissora (laboratório).
- Hash SHA-256 do PDF emitido (pra conferência).
- Sem PII do cliente final na página pública.

**Estados:**
- Token inválido: "certificado não encontrado".
- Vigente: badge verde.
- Substituída: badge laranja + link pra atual.

**Acessibilidade:** AA + PDF/UA quando baixa.
**Mobile:** prioritário (uso via câmera celular).

---

### Tela 8: Relatório de NC

**Propósito:** RT abre + acompanha NC.
**US:** `US-CER-008`.

**Elementos:**
- Lista NCs (filtros: origem, status, responsável, prazo).
- Editor: descrição, evidências (fotos/leituras), ação imediata, ação corretiva, responsável, prazo.
- Botão fechar NC (exige justificativa).

---

## Componentes reutilizáveis

- Pré-visualização PDF — compartilhado.
- Editor rich text limitado — compartilhado com Templates de outros módulos.
- Badge de status — compartilhado.

## Como esta lista evolui

- Tela nova → ligar a US.
- Mudança UX → CHANGELOG.
- Deprecada → `@deprecated`.
