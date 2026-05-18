---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-003
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-003.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-003 (Ficha 360° + QR dual-mode + PWA)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes do go-live público (não dogfooding) o texto da Tela "ativo de outro tenant"/"ativo Aferê" e a cláusula D4 do DPA (já cravada em `PRD-advogado.md`) precisam revisão de advogado humano com OAB ativa.

---

## Veredito

**APROVADO COM RESSALVAS (R1–R5).** O plano está sólido na arquitetura: dual-mode com 3 escopos cravado em `qr-publico-allowlist.md`, audit síncrono com `ip_hash`/`user_agent_hash`, resposta 404 indistinguível, rate limit + lockout, INV-AUTHZ-001/002/003 ativas. As ressalvas abaixo são ajustes finos de conformidade LGPD que **bloqueiam** promover a `stable`. Texto de UX só precisa um polimento (R5).

### Ressalvas

1. **R1 — Payload Escopo B do plano DIVERGE da allowlist canônica.** T-EQP-031 diz só "200 JSON Escopo B (allowlist)" sem fixar o contrato. Como a allowlist é a fonte da verdade legal (cláusula D4 do DPA — `dpa-modelo.md`), o plano precisa replicar **exatamente** os 6 campos do payload B e os 6 do payload C. Hoje o teste `test_payload_escopo_b_mostra_proxima_calibracao_mas_nao_pii` verifica `proxima_calibracao_em` + ausência de PII, mas **não trava** que o JSON contenha `faixa_medicao`, `classe_exatidao`, `mensagem` literal e `afere_url_institucional`. Sem snapshot do JSON exato, um agente de Wave A pode introduzir campo novo sem detectar — vira gap regulatório com ANPD. Ver §"Texto sugerido / contrato JSON" abaixo.
2. **R2 — `ip_hash` + `user_agent_hash` no scan anônimo (Escopo C) NÃO TEM `tenant_id` pra salgar.** T-EQP-030 manda "salgados por tenant (padrão INV-AUTHZ-002)" mas no Escopo C **não existe** tenant da sessão (o scan é anônimo, vindo do QR físico). Existe `tenant_id` do equipamento (cravado no hash HMAC), mas usar ele como salt **expõe escopo de enumeração**: dois atacantes em IP igual escaneando QRs de tenants diferentes geram hashes diferentes — o que é OK pra correlação interna, mas hash de IP "salgado por tenant do equipamento alvo" pode permitir a um insider do tenant Y **inferir** que um IP escaneou tenants X e Z (correlação cross-tenant via comparação de hashes em audit consolidado). Resposta correta: usar um **salt institucional do Aferê** (KMS-managed, `audit_ip_salt_global`) apenas para Escopo C, e manter `salt = HMAC(tenant_id, audit_ip_salt_global)` para Escopos A/B. Documentar essa decisão em `isolamento-multi-tenant.md` §8.1 (campo `ip_hash` ganha nota de exceção pra audit de QR anônimo). Mesma regra vale pra `user_agent_hash`.
3. **R3 — `Cache-Control: private, no-store` é suficiente, MAS faltam dois headers complementares pra cumprir LGPD art. 6º III (necessidade) + art. 46 (segurança).** Adicionar em T-EQP-031:
   - `Pragma: no-cache` — HTTP/1.0 legado; alguns proxies corporativos ainda respeitam só Pragma (clientes industriais com NAT enterprise).
   - `Expires: 0` — força revalidação em cache que ignore `Cache-Control`.
   - `Vary: Authorization, Cookie` — garante que CDN/proxy intermediário **nunca** sirva payload do Escopo A pra requisição do Escopo C (ou vice-versa) por confundir chaves de cache. Sem `Vary`, payload de tenant dono pode vazar pra anônimo via cache mal-configurado em proxy. Crítico.
   - `Referrer-Policy: no-referrer` — impede que ao clicar em `afere_url_institucional` o navegador vaze a URL do hash (que contém token opaco) pro destino.
   - `X-Robots-Tag: noindex, nofollow` — impede que crawler (Google, Bing) que tenha escaneado QR físico em foto pública indexe a URL com hash.
4. **R4 — Granularidade do log de visualização da ficha 360° (`equipamento.visualizado`) — gravar TODA abertura, não "primeira vez por sessão".** Replicar a decisão tomada em US-CLI-002 (INV-013 análoga): audit síncrono ANTES de renderizar, por acesso individual. T-EQP-034 diz "todo acesso à ficha 360° de outro perfil grava" — o "**de outro perfil**" está errado: ISO 17025 cl. 4.2 + INV-013 exigem log de TODA visualização **incluindo admin do próprio tenant** ("incluindo admins" é texto literal da INV-013 no `REGRAS-INEGOCIAVEIS.md` linha 43). Reescrever o AC: "todo acesso à ficha 360°, independente de papel do solicitante, grava `equipamento.visualizado` síncrono com `papel_visualizador`, `escopo_de_dados`, `categoria_dado_acessado` (enum US-CLI-002 R1), `ip_hash`, `purpose`". Sem isso, fiscalização ANPD com pergunta "quem viu o equipamento NS-XXX em 15/03/2027?" responde "não sei" — viola Art. 6º VI (transparência) + INV-013 + cl. 4.2 ISO 17025.
5. **R5 — Texto da tela do Escopo C diverge ligeiramente de E3 do `PRD-advogado.md`.** O `qr-publico-allowlist.md` §2 traz o JSON com mensagem "Este ativo está cadastrado no Aferê. Para acessar detalhes técnicos, entre em contato com o laboratório responsável." mas E3 do PRD-advogado tem texto mais cuidadoso: "**Este ativo está cadastrado no Aferê.** Para acessar os detalhes técnicos deste equipamento, entre em contato com o laboratório responsável. *Aferê é uma plataforma de gestão metrológica. Saiba mais em [https://afere.com.br].*" O segundo é o aprovado em revisão de PRD. Plano precisa garantir consistência (PWA + endpoint usam o mesmo texto). Para Escopo B, criar texto distinto (faltava no E3): "**Este ativo pertence a outro laboratório cadastrado no Aferê.** Próxima calibração em **{data}**. Detalhes técnicos protegidos por confidencialidade. *Aferê é uma plataforma de gestão metrológica. Saiba mais em [https://afere.com.br].*" Ver §"Textos UX prontos" abaixo.

### Não-ressalvas (validadas como corretas)

- ✅ **Audit síncrono no scan (T-EQP-030)** — alinhado com INV-AUTHZ-002 (gravar antes de retornar a resposta).
- ✅ **Resposta 404 indistinguível** (T-EQP-031) — espelho INV-051 e mitigação anti-oracle (mesma lógica que clientes Marco 1).
- ✅ **Rate limit + lockout** — atende `qr-publico-allowlist.md` §3 (60 req/min IP + 100 4xx em 1h → 24h bloqueio).
- ✅ **Timing constante** (risco 3 do plano) — defesa anti-timing-oracle correta; LGPD art. 46 (segurança).
- ✅ **PWA reusa `/v1/qr/{hash}`** — não cria novo endpoint público nem nova superfície LGPD; só cliente.
- ✅ **Stripping EXIF não é problema do scanner** (a foto entra em US-EQP-004); plano correto em não tocar.

---

## Texto sugerido / contrato JSON (cópia da `qr-publico-allowlist.md`)

**Escopo C (anônimo) — JSON exato:**
```json
{
  "tipo": "ativo_afere",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao",
  "mensagem": "Este ativo está cadastrado no Aferê. Para acessar os detalhes técnicos deste equipamento, entre em contato com o laboratório responsável.",
  "afere_url_institucional": "https://afere.com.br"
}
```

**Escopo B (outro tenant) — JSON exato:**
```json
{
  "tipo": "ativo_afere",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao",
  "proxima_calibracao_em": "YYYY-MM-DD|null",
  "faixa_medicao": "string|null",
  "classe_exatidao": "string|null",
  "mensagem": "Este ativo pertence a outro laboratório cadastrado no Aferê. Detalhes técnicos protegidos por confidencialidade.",
  "afere_url_institucional": "https://afere.com.br"
}
```

> **Observação ortográfica:** retirei o "ê" do nome de chave JSON (`afere_url_institucional` em vez de `aferê_url_institucional`). Chave JSON com caractere não-ASCII funciona tecnicamente mas quebra geradores de cliente (Flutter, TS, mypy stubs) em ferramentas que assumem ASCII. Atualizar a allowlist canônica também (CHANGELOG bump). O **valor** "Aferê" (com acento) fica nas mensagens visíveis ao usuário.

**Teste obrigatório adicional (acrescentar a T-EQP-036):**
- `test_payload_escopo_c_bate_exatamente_contrato_json` — snapshot test que compara payload retornado com JSON literal acima, byte a byte, ordem de chaves fixa.
- `test_payload_escopo_b_bate_exatamente_contrato_json` — idem.

---

## Textos UX prontos pra colar (PWA + endpoint)

### UX1 — Tela "ativo de outro tenant" (Escopo B)

> **Este ativo pertence a outro laboratório cadastrado no Aferê.**
>
> - Fabricante / Modelo: **{FABRICANTE} / {MODELO}**
> - Status: **{STATUS_LEGIVEL}**
> - Próxima calibração: **{PROXIMA_CALIBRACAO_DATA_BR}**
> - Faixa de medição: **{FAIXA}**
> - Classe de exatidão: **{CLASSE}**
>
> Detalhes técnicos completos (tag interna, número de série, histórico, cliente final, fotos) estão protegidos por confidencialidade entre laboratórios. Para mais informações sobre este ativo específico, contate o laboratório responsável pelo equipamento.
>
> _Aferê é uma plataforma de gestão metrológica. Saiba mais em [https://afere.com.br](https://afere.com.br)._

### UX2 — Tela "ativo Aferê — contate operador" (Escopo C)

> **Este ativo está cadastrado no Aferê.**
>
> - Fabricante / Modelo: **{FABRICANTE} / {MODELO}**
> - Status: **{STATUS_LEGIVEL}**
>
> Para acessar os detalhes técnicos deste equipamento, entre em contato com o laboratório responsável.
>
> _Aferê é uma plataforma de gestão metrológica de instrumentos de medição. Saiba mais em [https://afere.com.br](https://afere.com.br)._

### UX3 — Tela 404 (hash inválido / revogado / cross-tenant forjado) — indistinguível

> **QR Code não encontrado.**
>
> Este QR Code não corresponde a nenhum ativo cadastrado, foi atualizado ou está desativado. Verifique se você está escaneando o código mais recente fixado no equipamento.
>
> _Aferê — plataforma de gestão metrológica. [https://afere.com.br](https://afere.com.br)._

**Justificativas dos textos:**
- UX1 não revela nome do tenant dono (cláusula D4 do DPA) — só "outro laboratório".
- UX2 não cita tenant nem cliente final — atende `qr-publico-allowlist.md` §2 escopo C.
- UX3 unifica 3 cenários distintos em 1 mensagem — defesa anti-oracle de enumeração (cravada em risco 3 do plano).
- Todos os 3 mostram URL `afere.com.br` (institucional) mas sem fingerprint do tenant — atende LGPD art. 6º VI (transparência mínima) sem vazamento.

---

## Análise por área

### LGPD / Privacidade

- **Base legal do log de visualização da ficha 360°** (R4): art. 7º II (obrigação legal — INV-013 + cl. 4.2 ISO 17025) + art. 7º V (execução de contrato). Não é "consentimento". Granularidade "toda abertura, não primeira vez por sessão" é exigida porque INV-013 fala em "log de TODA visualização" — interpretação restritiva.
- **Base legal do `equipamento.qr_scanned`** (T-EQP-030): art. 7º III (interesse legítimo — controle de fraude/enumeração) + art. 46 (segurança). `ip_hash`/`ua_hash` salgados atende art. 6º III (necessidade — não armazenar IP cru) e art. 5º II (anonimização).
- **Categoria do dado tratado** (alinhar com US-CLI-002 R1): para `equipamento.qr_scanned` Escopo C/B → `metadado` (sem PII do visualizador identificável); para `equipamento.visualizado` Escopo A com payload completo → `pii_identificacao` (ficha contém CPF/CNPJ do cliente final). Categoria alimenta dashboard de drift e resposta a CIS ANPD.
- **`finalidade` / `purpose` no audit:** sempre preencher; para QR público use `controle_acesso_publico_pos_scan`; para ficha 360° use `execucao_contrato` (default) ou `obrigacao_legal` (se acesso é em contexto de auditoria/exportação).
- **Retenção:** `equipamento.qr_scanned` segue mesma matriz de audit (5 anos quente + WORM); `equipamento.visualizado` segue retenção do equipamento (5 anos pós-sucateamento ou 25 anos ISO 17025 se há certificado vinculado — atualizar `retencao-matriz.md` linha "equipamento_evento" se ainda não cobre).

### Contratual

- Cláusula D4 do DPA (`dpa-modelo.md`) já cobre QR Code público. Não precisa cláusula nova nesta US. A R1 (snapshot do JSON) é o teste que **comprova** cumprimento de D4 — sem snapshot, o DPA é decorativo.

### Regulatório (ANPD + ISO 17025)

- **Res. CD/ANPD 18/2024:** scan anônimo cai em "tratamento de dados de identificação técnica de coisa" — não dispara obrigação de DPO próprio. Mas o `ip_hash`/`ua_hash` no audit tornam o operador (Aferê) titular de dados acessórios — RAT-08 (audit) já cobre, sem RAT novo necessário.
- **Res. CD/ANPD 15/2024 (incidente):** se um vazamento expuser hashes consolidados de IP de scan público (cenário improvável: dump da `auditoria` via SQLi), R2 (salt institucional + salt por tenant) protege contra reidentificação. Sem R2, hash consolidado por equipamento permite correlação "este IP escaneou QRs de 50 equipamentos do tenant X" → fingerprinting.
- **ISO 17025 cl. 4.2 (confidencialidade):** R4 (granularidade total do log) é a única forma de cumprir "acesso a dados de cliente do laboratório só com permissão explícita **+ log de toda visualização (incluindo admins)**".

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Snapshot do JSON ausente → agente Wave A introduz campo novo no payload B/C sem perceber → vaza PII | Alta sem R1 | NC LGPD + violação cláusula D4 do DPA | R1 — `test_payload_escopo_{b,c}_bate_exatamente_contrato_json` (snapshot byte a byte) |
| `ip_hash` salgado por tenant do equipamento permite correlação cross-tenant em dump consolidado | Média | Re-identificação parcial de IPs de visitantes | R2 — salt institucional para Escopo C + `HMAC(tenant_id, salt_global)` para A/B |
| Cache CDN mal-configurado serve payload A pra requisição C (ou vice-versa) | Baixa mas catastrófica | Vazamento massivo PII (todos os ativos públicos viram visíveis) | R3 — `Vary: Authorization, Cookie` + `Pragma` + `Expires: 0` + `Referrer-Policy: no-referrer` + `X-Robots-Tag: noindex` |
| Log de visualização só "de outro perfil" — fiscalização ANPD pergunta "quem viu este equipamento?" e admin não aparece | Alta sem R4 | NC LGPD + NC ISO 17025 cl. 4.2 | R4 — log de TODA visualização, sem filtro por papel |
| Texto da Tela C revela tenant dono por algum slug/logo | Baixa (PWA bem implementada) mas alta se descuido | NC cláusula D4 do DPA + ressentimento de cliente | R5 — UX1/UX2/UX3 com textos fixos, logo Aferê institucional, sem branding do tenant |
| URL com hash opaco vaza via Referer ao clicar em `afere_url_institucional` → terceiro recebe token | Média | Hash reaproveitável + audit poluído | R3 — `Referrer-Policy: no-referrer` |
| Crawler de buscador indexa hash (foto pública de QR físico em LinkedIn/Instagram) | Média | Hash listado em Google → enumeração facilitada | R3 — `X-Robots-Tag: noindex, nofollow` |

---

## Próximos passos

- Aplicar R1–R5 no plano `US-EQP-003.md` (autoria: implementador da Wave A — tech-lead).
- Atualizar `qr-publico-allowlist.md`: trocar `aferê_url_institucional` → `afere_url_institucional` no JSON (bump CHANGELOG); inserir nota em §3 sobre salt institucional do Aferê para Escopo C + salt composto para A/B.
- Atualizar `isolamento-multi-tenant.md` §8.1: campo `ip_hash` ganha nota "exceção QR anônimo — salt institucional" (referência cruzada com R2 deste parecer).
- Inserir UX1/UX2/UX3 no PRD `equipamentos` §UI (Tela 4 — Scan QR) — substituir E3 atual.
- Acrescentar 2 testes de snapshot a T-EQP-036 (escopo B + escopo C).
- ⚠️ **Antes do go-live público** (não MVP-1 dogfooding): textos UX1/UX2/UX3 PRECISAM revisão de advogado humano com OAB ativa porque serão exibidos a milhões de visitantes (qualquer pessoa que escanear um QR físico). Recomendo consulta pontual com advogado LGPD (perfil: experiência em SaaS B2B operador + privacy by design); preparei este parecer + `qr-publico-allowlist.md` + `dpa-modelo.md` D4 pra otimizar o tempo dele/dela (estimado 1-2h de revisão).

---

## Referências normativas

- Lei 13.709/2018 (LGPD) — art. 5º II, 6º III/VI, 7º II/III/V, 46
- Res. CD/ANPD 15/2024 — incidentes
- Res. CD/ANPD 18/2024 — DPO
- ISO/IEC 17025:2017 cl. 4.2 (confidencialidade) + cl. 8.4 (retenção)
- INV-013, INV-051, INV-AUTHZ-001/002/003, INV-TENANT-001/002 (`REGRAS-INEGOCIAVEIS.md`)
- `docs/conformidade/equipamentos/qr-publico-allowlist.md` (cláusula D4 técnica)
- `docs/conformidade/comum/dpa-modelo.md` (D4 contratual)
- `docs/conformidade/comum/isolamento-multi-tenant.md` §8 (audit tables)
- `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-002-advogado.md` (R1 categoria + granularidade — base de R4)
- ADR-0012 (porta AuthorizationProvider) + ADR-0018 (PWA scanner)
