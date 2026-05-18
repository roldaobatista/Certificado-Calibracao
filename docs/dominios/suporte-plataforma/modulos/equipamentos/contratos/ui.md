---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Contratos de UI — Equipamentos do cliente

> **v2 (2026-05-18):** revisão dos 4 subagentes — Tela 5 vira PWA (ADR-0018), telas ganham camadas de visibilidade por papel (RBC C8), Tela 6 (Recebimento) nova, todos textos UX prontos pra colar.

## Telas

### Tela 1: Lista de equipamentos

**Propósito:** localizar equipamento em ≤ 30s.
**Persona:** metrologista, atendente, almoxarife.
**US:** US-EQP-001, US-EQP-003.
**Stack:** HTMX sobre Django templates (ADR-0010).

**Elementos:**
- Campo busca (TAG, NS, cliente).
- Filtros: status, cliente, próxima calibração vencendo, perfil_tenant_no_cadastro.
- Botão "novo equipamento" (visível a quem tem `equipamento.criar`).
- Tabela: TAG, NS, modelo, cliente_atual, status, próxima calibração.
- Ação por linha: abrir ficha / imprimir QR / re-emitir QR / transferir.

**Escopo de listagem por papel (advogado C3):**
- `admin_tenant`, `metrologista`: lista qualquer cliente.
- `atendente`: lista apenas clientes com OS aberta ou últimos 90d.
- `tecnico_campo`: lista apenas equipamentos das OSs atribuídas.

**Estados:**
- Vazio: "nenhum equipamento cadastrado — cadastrar primeiro".
- Erro: "não foi possível carregar a lista, tentar novamente".

---

### Tela 2: Cadastro/Edição de equipamento

**Propósito:** criar ou editar equipamento.
**US:** US-EQP-001, US-EQP-002.
**Stack:** HTMX + Django forms.

**Elementos:**
- Campos: cliente (obrigatório, autocompletar restrito ao tenant), TAG (validação ao vivo de unicidade no tenant — INV-049), NS, fabricante, modelo, faixa, classe, descrição, **localização física** (validação anti-PII), material_etiqueta (combo).
- Em modo edição com cert emitido: campos imutáveis (TAG, NS, fabricante, perfil_tenant_no_cadastro) aparecem cinza com tooltip "não pode alterar — equipamento já tem certificado emitido".
- Em modo edição com cert emitido + altera classe_exatidao/faixa_medicao + perfil A: combo `motivo_mudanca` (enum) + campo `motivo_detalhe` + botão "assinar com A3" (workflow A3 RT obrigatório).
- Botão "salvar e imprimir etiqueta" (combina criar + chamar `/qr` PDF).

**Aviso campo `localizacao_fisica` (texto pronto — advogado E2):**
> **Local físico do equipamento (até 200 caracteres)**
> Exemplo: *"Almoxarifado A — prateleira 3"*, *"Laboratório de qualidade — bancada 2"*.
> Não inclua **nomes de pessoas** — esses ficam no cadastro do cliente. CPF, e-mail e telefone também não devem aparecer aqui.

**Erro de validação anti-PII:**
> *"Identifiquei dados pessoais no texto (CPF, e-mail, telefone ou nome). Reescreva apenas com a localização física do equipamento — os dados do cliente já estão no cadastro dele."*

**Aviso edição com cert emitido (texto pronto — advogado E5):**
> **Atenção:** este equipamento já possui certificado de calibração emitido.
> Alterações em **modelo**, **faixa de medição**, **classe**, **descrição** ou **localização** criarão uma **nova versão** do registro. Os certificados anteriores continuam vinculados à versão original — isso é exigência da norma ISO/IEC 17025 cl. 8.4.
> Campos **TAG**, **número de série** e **fabricante** não podem ser alterados após emissão de certificado.

---

### Tela 3: Ficha 360° do equipamento

**Propósito:** ver tudo do equipamento numa tela.
**US:** US-EQP-003.
**Acessível por:** lista, QR Code, busca global, link em OS.
**Stack:** HTMX + Django.

**Camadas de visibilidade por papel (RBC C8):**

| Aba/seção | metrologista | atendente | almoxarife | técnico_campo |
|---|:---:|:---:|:---:|:---:|
| Cabeçalho (TAG, status, cliente, próx. calibração) | ✅ | ✅ | ✅ | ✅ |
| Aba Dados (atributos + versões) | ✅ | ✅ | ✅ | ✅ |
| Aba Histórico de calibração (via porta) | ✅ | ✅ | ✅ | ✅ |
| Aba OS abertas (via porta) | ✅ | ✅ | ✅ | ✅ (só atribuídas) |
| Aba Eventos (audit log) | ✅ | ❌ | ❌ | ❌ |
| Aba Recebimentos (fotos chegada/devolução + decisões) | ✅ | ❌ | ✅ | ❌ |
| Botão "imprimir etiqueta" | ✅ | ✅ | ✅ | ❌ |
| Botão "sucatear" | ✅ | ❌ | ❌ | ❌ |
| Botão "transferir cliente" | ✅ | ✅ | ❌ | ❌ |
| Botão "re-emitir QR" | ✅ | ❌ | ❌ | ❌ |

**Após transferência (cessionário visualizando — RBC B6):**
- Aba "Histórico de calibração" mostra apenas certificados emitidos a partir da transferência.
- Banner: "Equipamento adquirido de terceiro em DD/MM/AAAA. Histórico anterior preservado mas confidencial — solicite ao cliente cedente."

**Performance:** p95 ≤ 1.5s.

---

### Tela 4: Impressão de etiqueta (PDF)

**Propósito:** gerar PDF da etiqueta com QR.
**Elementos:** QR + TAG + NS + logo tenant + número da etiqueta de calibração atual (se há).
**Tamanho:** A6 default; label 50x80mm opcional.
**Material:** conforme `material_etiqueta` (poliéster laminado / vinil térmico / metálica alumarca).

---

### Tela 5: Scanner QR — PWA (ADR-0018)

**Propósito:** abrir ficha via celular ou desktop sem app nativo.
**US:** US-EQP-003.
**Stack:** PWA (HTML + JS vanilla) + BarcodeDetector API + fallback jsQR.

**Elementos:**
- Tela explicativa antes da permissão de câmera ("vamos abrir a câmera pra ler o QR Code colado no equipamento").
- Botão "escanear" → solicita permissão câmera.
- Visor câmera ativo (`facingMode: 'environment'`).
- Detecção bem-sucedida → redireciona pra `/v1/qr/{hash}` (resolução dual-mode pelo backend).
- Permissão negada → fallback: `<input type="file" accept="image/*" capture="environment">` + jsQR decoda imagem estática.

**Estados:**
- Sem permissão câmera + sem fallback: "Não conseguimos ler QR Code neste navegador. Tente abrir noutro celular ou peça ajuda ao operador."
- QR válido + mesmo tenant: redireciona pra ficha 360° (Tela 3).
- QR válido + outro tenant / anônimo: Tela 7 (scan público).
- QR inválido / revogado: "QR Code não encontrado ou foi atualizado. Peça uma nova etiqueta ao operador."

**Acessibilidade:** instruções por voz opcionais; texto alto contraste.

---

### Tela 6: Recebimento físico no laboratório (US-EQP-006 — RBC B1/B2)

**Propósito:** registrar entrada física do equipamento + condição visual + foto + decisão sobre anomalias.
**Persona:** almoxarife (P-OP-03), metrologista.
**Stack:** HTMX + câmera nativa do navegador (foto).

**Elementos:**
- Identificação: equipamento existente (busca por TAG/NS) OU criar cadastro provisório.
- Campos: `condicao_visual_chegada` (radio enum), `lacre_chegada` (texto opcional), `anomalias_observadas` (textarea).
- Upload de fotos (≥1 obrigatória em perfil A; opcional B/C/D) — câmera ou arquivo.
- Se condição != integro: aparecem `decisao_apos_anomalia` (combo) + `justificativa_decisao` (≥30 chars).
- Botão "registrar recebimento" → cria `EquipamentoRecebimento`.

**Aviso UX antes da câmera (texto pronto — advogado E1):**
> **Antes de tirar a foto**
> Fotografe apenas o equipamento e, quando necessário, o ambiente técnico (lacre, dano, plaqueta).
> **Evite capturar:**
> - rosto de pessoas (funcionários, clientes ou terceiros);
> - documentos, telas de computador ou crachás;
> - quadros com informações pessoais ao fundo.
>
> A imagem ficará vinculada ao equipamento e poderá ser visualizada por outros usuários autorizados da sua empresa. Se uma pessoa identificável aparecer por engano, exclua e refaça a foto.
> [ Continuar ] [ Cancelar ]

**Após upload:** EXIF removido server-side automaticamente; UI confirma "foto salva — dados de localização removidos automaticamente".

---

### Tela 7: Scan público sem sessão (Escopo B/C — advogado E3)

**Propósito:** mostrar mensagem genérica quando QR é escaneado sem sessão do tenant dono.

**Texto (Escopo C — anônimo):**
> **Este ativo está cadastrado no Aferê.**
> Para acessar os detalhes técnicos deste equipamento, entre em contato com o laboratório responsável.
>
> _Aferê é uma plataforma de gestão metrológica. Saiba mais em [https://afere.com.br]._
>
> *(Sem identificação do tenant, sem TAG, sem foto, sem localização — conforme `qr-publico-allowlist.md`.)*

**Texto (Escopo B — outro tenant):**
> **Ativo de outro laboratório.**
> Este equipamento pertence a outro tenant da plataforma. Detalhes técnicos protegidos por confidencialidade.
> Fabricante: {fabricante} · Modelo: {modelo} · Status: {status} · Próxima calibração: {data}.

---

### Tela 8: Aceite de transferência (cessionário — US-EQP-004 / advogado E4)

**Propósito:** capturar aceite formal do cliente cessionário antes de a transferência ser confirmada.
**Persona:** cliente final cessionário (via portal cliente — módulo `portal-cliente`).

**Texto:**
> **Aceite de transferência de equipamento**
> O laboratório **[Razão Social do Tenant]** registrou a transferência do equipamento abaixo do cliente **[CEDENTE — descrição genérica]** para você:
>
> - TAG: **{TAG}**
> - Número de série: **{NS}**
> - Fabricante / Modelo: **{FABRICANTE} / {MODELO}**
> - Motivo da transferência: **{MOTIVO_CATEGORIA_LEGIVEL}**
>
> Ao aceitar, você assume a titularidade operacional deste equipamento perante o laboratório, incluindo a responsabilidade pela calibração e manutenção futuras. **Esta transferência não inclui certificados anteriores nem responsabilidades fiscais ou trabalhistas do cedente.**
>
> [ Aceitar transferência ] [ Recusar ] [ Falar com o laboratório ]
>
> *Lei 14.063/2020 — Sua aceitação digital é registrada com data, hora e identificador do dispositivo.*

**Tela paralela para o cedente:** texto análogo "autorize a transferência" com `motivo_categoria` legível.

---

## Acessibilidade

- WCAG AA em todas as telas HTMX.
- PWA scanner (Tela 5): navegação por teclado opcional; instruções por voz; alto contraste.
- Textos alt em ícones; foco visível.

## Mobile

- Tela 3 (Ficha 360°), Tela 5 (Scanner QR), Tela 6 (Recebimento) — responsivas + PWA.
- App Flutter Wave B (ADR-0003) reusa endpoints `/v1/equipamentos/{id}` e `/v1/qr/{hash}`.

## Como evolui

- Tela nova → linkar US-EQP-NNN.
- Mudança UX → bump CHANGELOG.
- Adição de papel novo → atualizar tabela de camadas de visibilidade (Tela 3).
