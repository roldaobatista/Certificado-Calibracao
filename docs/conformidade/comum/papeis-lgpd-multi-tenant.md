---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
relacionados:
  - docs/conformidade/comum/dpa-modelo.md
  - docs/conformidade/comum/finalidades-lgpd.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
---

# Papéis LGPD em SaaS multi-tenant (4-party data)

> **Origem:** TEMA-D.10 da auditoria 10 lentes 2026-05-23. Modelo atual trata `cliente_id` neutro mas em LGPD há até 4 papéis envolvidos. Sem mapeamento, contratos DPA ficam ambíguos e responsabilidades não rastreadas.

---

## 1. Os 4 papéis presentes na operação

Cenário típico: tenant é um laboratório de calibração. Seu cliente é uma indústria farmacêutica. Na indústria há um contato (pessoa física que assina) e talvez o titular final do dado (o paciente final que receberá o medicamento medido com balança calibrada pelo lab).

| Papel | Quem | Função LGPD | Exemplo |
|---|---|---|---|
| **Vendor (Aferê)** | Pessoa jurídica fornecedora do SaaS | **Operador** (art. 5º VII LGPD) sob o tenant | Recebe dados de cliente PF/PJ via tenant; processa pra entregar funcionalidade do SaaS |
| **Tenant** | Pessoa jurídica que contrata o SaaS (laboratório) | **Controlador** (art. 5º VI) — decide finalidades + meios | Cadastra clientes, manda OS, emite certificados |
| **Cliente final do tenant** | PF ou PJ que contratou serviço do tenant | **Titular** (art. 5º V) quando PF; **Sub-controlador** quando PJ (controla dados de seus próprios contatos) | Empresa farmacêutica X cliente do laboratório |
| **Contato PF dentro do cliente PJ** | Pessoa física que assina, recebe e-mail, dá aceite | **Titular** (sempre) | Maria Silva, gerente de qualidade da empresa farmacêutica X |

## 2. Cadeia de controle de dado

```
[Vendor Aferê] ←── operador ── [Tenant laboratório] ── controlador → cadastra ── [Cliente PJ] ── controlador → fornece ── [Contato PF]
                                                                                                                            ↓ titular
                                                                                                                       PII direta
```

- **Vendor Aferê** recebe TODOS os dados via integração com o tenant; responde como operador da LGPD por ele.
- **Tenant** é o controlador na perspectiva LGPD — responde diretamente perante ANPD se incidente afeta cliente do tenant.
- **Cliente PJ** é sub-controlador dos seus próprios contatos PF (LGPD art. 5º VI extensão).
- **Contato PF** é titular direto da PII (nome, e-mail, telefone, CPF se coletado).

## 3. Responsabilidades por papel

### Aferê (vendor / operador)

- Cumprir instruções do tenant (DPA padrão).
- Garantir segurança técnica (criptografia, RLS, audit log, retenção).
- Notificar tenant em até 24h se houver incidente afetando dados do cliente do tenant.
- **NÃO** decide finalidade (art. 5º VII LGPD).

### Tenant (laboratório / controlador)

- Decide bases legais por categoria de dado coletado de cliente PJ + contato PF.
- Publica seu DPO + canal de titular (INV-006).
- Mantém DPA atualizado com cada cliente PJ (responsabilidade do tenant — Aferê NÃO assina por ele).
- Notifica ANPD em ≤3 dias úteis em caso de incidente afetando cliente (INV-005).

### Cliente PJ (sub-controlador)

- Mantém DPA com seus próprios titulares (contatos PF).
- Decide o que compartilha com o tenant.
- Aferê NÃO se comunica diretamente com clientes PJ — sempre via tenant.

### Contato PF (titular)

- Exerce direitos do art. 18 LGPD direto ao cliente PJ (não ao tenant nem ao vendor).
- Vai indireto ao tenant se cliente PJ não responder.

## 4. Cláusulas obrigatórias no DPA padrão Aferê↔Tenant

> Ver `docs/conformidade/comum/dpa-modelo.md`. Esta seção destaca cláusulas que **decorrem do mapeamento 4-party**.

- **Cláusula 4.2** — Aferê processa dados em nome do tenant; nunca usa pra finalidade própria; nunca compartilha com terceiros exceto sub-operadores listados.
- **Cláusula 4.3** — Aferê notifica tenant de incidente em ≤ 24h; tenant decide quando notificar ANPD/titular.
- **Cláusula 4.4** — Direito de auditoria do tenant sobre Aferê (1x/ano + emergencial em incidente).
- **Cláusula 4.5** — Sub-operadores listados (Backblaze B2, AWS KMS, Hostinger, etc.) — qualquer mudança exige aviso prévio ao tenant + cláusula equivalente.
- **Cláusula 4.6** — Aferê **NÃO se responsabiliza pelos DPA do tenant↔cliente PJ** — esse contrato é responsabilidade do tenant.
- **Cláusula 4.7** — Em caso de eliminação solicitada por titular PF, Aferê aplica matriz `eliminacao_efetiva` vs `anonimizacao_em_lugar` conforme ADR-0021 (3 zonas A/B/C); tenant aprova caso a caso quando zona ambígua.

## 5. Cláusulas obrigatórias no DPA padrão Tenant↔Cliente PJ

> Modelo a ser usado pelo tenant; Aferê fornece template como serviço de valor agregado mas **NÃO assina** por ele.

- Identificação do controlador (cliente PJ).
- Identificação do operador (tenant laboratório).
- Categorias de dados pessoais tratados (lista por sistema).
- Finalidades específicas (calibração, manutenção, certificação).
- Sub-operadores (Aferê + sub-operadores do Aferê).
- Direitos do titular + canal de exercício.
- Cláusula de geolocalização (técnico vai ao endereço do cliente PJ — RAT-07).
- Cláusula de fotos com EXIF (matriz retenção + INV-OS-GEO-001).
- Prazo de notificação de incidente entre as partes.

## 6. Cenários de exercício de direito do titular

### Cenário A: titular PF (contato dentro do cliente PJ) pede eliminação ao tenant

1. Tenant recebe pedido (ex: via canal LGPD do tenant).
2. Tenant valida com cliente PJ (sub-controlador) se há obrigação legal de retenção.
3. Tenant aplica matriz ADR-0021:
   - Zona A (sem cert/NF emitido): elimina via comando ao Aferê.
   - Zona B (com cert/NF): anonimiza CPF/nome (preserva CREA/competência) — Aferê processa.
   - Zona C (ambígua): tenant decide com aval do cliente PJ.
4. Aferê executa instrução do tenant (operador) e gera audit log do processamento.

### Cenário B: titular PF pede eliminação direto ao Aferê

1. Aferê **NÃO atende diretamente** (art. 18 LGPD: titular vai ao controlador).
2. Aferê responde "encaminhe ao DPO do laboratório [nome] em [contato]".
3. Aferê notifica tenant da tentativa (transparência).

### Cenário C: Aferê descobre vazamento

1. Aferê notifica tenant em ≤ 24h (DPA cl. 4.3).
2. Tenant decide ANPD + titular (INV-005 — em ≤3 dias úteis).
3. Aferê coopera com investigação + audit log.

## 7. Implicações pro modelo de domínio

- `Cliente` (no modelo OS/Calibração) representa o **Cliente PJ** ou **Cliente PF direto** do tenant.
- `Cliente.contato_pf_id` aponta pra entidade `ContatoCliente` (PF dentro do cliente PJ — futura entidade Wave A se necessário).
- Para PF, `Cliente.tipo = "PF"` e o titular = o próprio cliente.
- Para PJ, `Cliente.tipo = "PJ"` e o(s) titular(es) são `ContatoCliente`(s).

## 8. Pendências

- [ ] Criar entidade `ContatoCliente` no modelo de Cliente (Marco 1 ou Wave A — se necessário pra emissão de cert que cite contato PF).
- [ ] Hook `dpa-cliente-pj-required.sh` validando que tenant carrega flag de DPA assinado com cliente PJ antes de emitir cert.
- [ ] Painel "Status DPA" no admin do tenant.
