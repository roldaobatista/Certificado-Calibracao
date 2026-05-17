---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Contratos de UI — Equipamentos do cliente

## Telas

### Tela 1: Lista de equipamentos

**Propósito:** localizar equipamento em ≤ 30s.
**Persona:** metrologista, atendente.
**US:** US-EQP-001, US-EQP-003.
**Acessível por:** menu "Equipamentos" + busca global.

**Elementos:**
- Campo busca (TAG, NS, cliente)
- Filtros: status, cliente, próxima calibração vencendo
- Botão "novo equipamento"
- Tabela: TAG, NS, modelo, cliente, status, próxima calibração
- Ação por linha: abrir ficha / imprimir QR

**Estados:**
- Vazio: "nenhum equipamento cadastrado — cadastrar primeiro"
- Erro: "não foi possível carregar a lista, tentar novamente"

---

### Tela 2: Cadastro/Edição de equipamento

**Propósito:** criar ou editar equipamento.
**US:** US-EQP-001, US-EQP-002.

**Elementos:**
- Campos: cliente (obrigatório), TAG, NS, fabricante, modelo, faixa, classe, descrição, localização
- Botão "salvar e imprimir etiqueta"
- Em modo edição: campos imutáveis (TAG, NS, fabricante) aparecem em cinza com tooltip "não pode alterar — equipamento já tem certificado emitido"

**Estados:**
- Edição com cert. emitido: aviso topo "alterações em modelo/faixa/classe criarão uma nova versão; certificados anteriores referenciam a versão atual"
- Erro 422 (INV-025): mensagem PT "não é possível alterar TAG após emissão de certificado"

---

### Tela 3: Ficha 360° do equipamento

**Propósito:** ver tudo do equipamento numa tela.
**US:** US-EQP-003.
**Acessível por:** lista, QR Code, busca global, link em OS.

**Elementos:**
- Cabeçalho: TAG, NS, status, cliente atual, próxima calibração
- Aba "Dados": atributos atuais + link para versões anteriores
- Aba "Histórico de calibração": tabela com data, certificado, padrão usado
- Aba "OS abertas": OS em andamento
- Aba "Eventos": log imutável
- Botão "imprimir etiqueta", "sucatear", "transferir cliente"

**Performance:** p95 ≤ 1.5s.

---

### Tela 4: Impressão de etiqueta (PDF)

**Propósito:** gerar PDF da etiqueta com QR.
**Elementos:** QR + TAG + NS + logo tenant. Tamanho A6 ou label 50x80mm.

---

### Tela 5 (mobile): Scanner QR

**Propósito:** abrir ficha via celular.
**US:** US-EQP-003.

**Elementos:** botão "escanear", câmera ativa, ao detectar QR redireciona para ficha 360° mobile.
**Estado erro:** "QR inválido ou equipamento foi removido".

---

## Acessibilidade

WCAG AA. Navegação por teclado obrigatória. Textos alt em ícones.

## Mobile

Responsivo + função scanner QR via PWA/app (ver ADR-0003).

## Como evolui

- Tela nova → linkar US-EQP-*.
- Mudança UX → bump CHANGELOG.
