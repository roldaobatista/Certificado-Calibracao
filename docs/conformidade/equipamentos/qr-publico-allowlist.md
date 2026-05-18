---
owner: claude-code
revisado-em: 2026-05-18
status: stable
escopo: módulo equipamentos — política de exposição de campos via QR Code público
---

# QR Code público de equipamento — allowlist de campos por escopo de sessão

> **Pra quê:** o QR Code do equipamento fica **fisicamente colado no instrumento** — qualquer pessoa que se aproxime escaneia. Faxineira, visitante, técnico de empresa concorrente, terceirizado. **A confidencialidade dos dados depende inteiramente da camada de autenticação operada pelo Aferê** (cláusula D4 do DPA — `docs/conformidade/comum/dpa-modelo.md`).
>
> **Origem:** parecer subagente `advogado-saas-regulado` (B3 — espelho INV-035 de certificados públicos) + parecer subagente `tech-lead-saas-regulado` (B2 — dual-mode) + parecer subagente `corretora-seguros-saas` (B1 — modelo de ameaça) durante auditoria PRD `equipamentos` Wave A Marco 2 (2026-05-18).
>
> **INV cravada:** [INV-051](../../../REGRAS-INEGOCIAVEIS.md) — token opaco HMAC-SHA256 + allowlist por modo.

---

## 1. Três escopos de sessão (resolve `GET /v1/qr/{hash}`)

1. **Escopo A — Sessão autenticada no MESMO tenant do equipamento.**
   - Usuário operacional do tenant dono (metrologista, atendente, almoxarife, técnico de campo, admin).
   - Resolução de hash retorna **302 redirect** para ficha 360° completa (Tela 3).
   - Log de visualização (`equipamento.visualizado` — INV-013 análoga) em audit.

2. **Escopo B — Sessão autenticada em OUTRO tenant.**
   - Usuário operacional de tenant diferente. Caso real: técnico de campo de tenant X que faz manutenção em equipamento de tenant Y por acordo comercial.
   - Resolução retorna **200 com payload mínimo** (mesmo do anônimo, por enquanto — `tenant_compartilhamento` é Wave B+ se demanda real surgir).
   - Log do scan + decisão `denied_cross_tenant` em audit.

3. **Escopo C — Sessão anônima ou nenhuma sessão.**
   - Qualquer pessoa que escaneie o QR físico sem login.
   - Resolução retorna **200 com payload mínimo público**.
   - Log do scan + IP hash + user-agent hash em audit.

---

## 2. Tabela de campos por escopo

> **Regra mestre:** se está marcado **NÃO** em alguma coluna, o campo **NÃO PODE** aparecer no payload daquele escopo. O backend filtra antes de serializar — nunca confia no frontend.

| Campo / dado | Escopo A (mesmo tenant) | Escopo B (outro tenant) | Escopo C (anônimo) |
|---|:---:|:---:|:---:|
| Nome do cliente final (PF ou razão social PJ) | SIM | NÃO | NÃO |
| CPF / CNPJ do cliente final | SIM | NÃO | NÃO |
| Telefone / e-mail do cliente | SIM | NÃO | NÃO |
| Endereço completo do cliente | SIM | NÃO | NÃO |
| Razão social / nome fantasia do tenant dono | SIM | NÃO | NÃO |
| TAG do equipamento (interna do tenant) | SIM | NÃO | NÃO |
| Número de série completo do equipamento | SIM | NÃO | NÃO |
| Fabricante + modelo do equipamento | SIM | SIM (genérico) | SIM (genérico) |
| Status (ativo / inativo / sucata / em_calibracao) | SIM | SIM | SIM |
| Data da próxima calibração | SIM | SIM | NÃO |
| Foto do equipamento | SIM | NÃO | NÃO |
| Localização física (`localizacao_fisica`) | SIM | NÃO | NÃO |
| Faixa de medição / classe de exatidão | SIM | SIM | NÃO |
| Histórico de certificados (lista) | SIM | NÃO | NÃO |
| Histórico de OS abertas / fechadas | SIM | NÃO | NÃO |
| Versões anteriores do equipamento | SIM | NÃO | NÃO |
| Eventos do equipamento (transferências, edições) | SIM | NÃO | NÃO |
| Mensagem genérica "este ativo está cadastrado no Aferê" | n/a | SIM | SIM |
| Link / convite "contate o operador para detalhes" | n/a | SIM | SIM |
| Logo Aferê institucional | n/a | SIM | SIM |
| Logo / branding do tenant dono | SIM | NÃO | NÃO |

**Resumo do payload Escopo C (anônimo) — JSON exato:**

```json
{
  "tipo": "ativo_aferê",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao",
  "mensagem": "Este ativo está cadastrado no Aferê. Para acessar detalhes técnicos, entre em contato com o laboratório responsável.",
  "aferê_url_institucional": "https://afere.com.br"
}
```

Note: `status` aparece em alto nível pra que um terceiro escaneando consiga distinguir "este QR ainda é válido" vs "QR de equipamento sucateado" — útil pra IPEM/auditoria externa que precisa validar se o ativo está em uso. Não vaza nada sobre o cliente.

**Resumo do payload Escopo B (outro tenant) — JSON exato:**

```json
{
  "tipo": "ativo_aferê",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao",
  "proxima_calibracao_em": "YYYY-MM-DD|null",
  "faixa_medicao": "string|null",
  "classe_exatidao": "string|null",
  "mensagem": "Este ativo pertence a outro tenant da plataforma Aferê. Detalhes técnicos protegidos por confidencialidade.",
  "aferê_url_institucional": "https://afere.com.br"
}
```

---

## 3. Defesa em profundidade — controles obrigatórios

| Camada | Controle | Onde implementa |
|---|---|---|
| **Token** | HMAC-SHA256 sobre `(equipamento_id, tenant_id, emitido_em_iso8601)` + KMS_qr_secret; ≥128 bits entropia; base64url ≥22 chars | `src/infrastructure/equipamentos/qr_token.py` (a criar Wave A) |
| **Segredo** | `KMS_qr_secret` em AWS KMS MRK (sa-east-1 ↔ us-east-1); rotação anual; rotação NÃO invalida hashes existentes (validação consulta tabela, não recomputa) | AWS console + `src/infrastructure/kms/qr_secret.py` |
| **Autenticação** | `AuthorizationProvider.can(...)` decide escopo A/B/C com `purpose='leitura_publica_pos_scan'` para B/C | `src/infrastructure/authz/...` |
| **Rate limit por usuário** | 60 req/min/usuário autenticado | Django Ratelimit |
| **Rate limit por IP** | 60 req/min/IP independente de autenticação | Django Ratelimit + nginx |
| **Lockout** | IP que gerou 100+ respostas 4xx em 1h fica bloqueado por 24h | nginx + alerta P2 |
| **Resposta indistinguível** | 404 idêntico para "hash inválido" e "hash de outro tenant" (sem oracle de enumeração) | Camada view antes de hit DB |
| **Audit** | Todo scan logado (escopo A/B/C) com IP hash + user-agent hash + decisão | `audit_trail.eventos` action=`equipamento.qr_scanned` |
| **Revogação automática** | Re-emissão de QR seta `revogado_em = now()` no anterior; flag explícita `manter_anterior_ativo` por 90 dias máx em caso de re-impressão em lote | `src/application/equipamentos/qr_emissao.py` |

---

## 4. Anti-padrões proibidos

- ❌ Slug humano-legível na URL (ex: `/qr/balanca-toledo-2024`). Sempre token opaco.
- ❌ TAG ou NS visível no payload do hash (sem cifrar).
- ❌ Endpoint retorna mensagem distinta para "QR válido outro tenant" vs "QR não existe" — vira oracle.
- ❌ Renderizar lado-cliente decidindo o que esconder (regra do payload é server-side, sempre).
- ❌ Cachear payload completo CDN (`Cache-Control: public`) — payload varia por escopo, exige `Cache-Control: private, no-store`.
- ❌ Hash sem `tenant_id` no payload — permite reuso cross-tenant se segredo vazar.

---

## 5. Validação / testes obrigatórios

| ID | Teste | Esperado |
|---|---|---|
| T-QR-PUB-01 | Scan anônimo de QR válido | 200 com JSON exato da seção 2 (Escopo C); audit registrou IP hash |
| T-QR-PUB-02 | Scan autenticado outro tenant | 200 com JSON exato Escopo B; audit decisão `denied_cross_tenant` |
| T-QR-PUB-03 | Scan autenticado mesmo tenant | 302 redirect pra `/equipamentos/{id}` (ficha 360°) |
| T-QR-PUB-04 | Hash inválido (random 22 chars base64url) | 404 idêntico ao "hash de outro tenant" |
| T-QR-PUB-05 | Enumeração: 100 hashes aleatórios em 1min | Após o 60º → 429; após 100 4xx em 1h → IP bloqueado 24h |
| T-QR-PUB-06 | Cross-tenant fuzzing: gerar hash com tenant_id de outro tenant manualmente | 404 (HMAC inválido com KMS_qr_secret) |
| T-QR-PUB-07 | Re-emissão revoga anterior automaticamente | Hash antigo → 404; hash novo → 302/200 |
| T-QR-PUB-08 | Payload escopo C **não contém** nenhum dos campos PROIBIDOS (varredura regex) | Bateria com 20 nomes/CPFs/e-mails plantados em fixture; nenhum aparece |
| T-QR-PUB-09 | Status `sucata` em escopo C ainda retorna status (não vaza outras coisas) | JSON com `status: "sucata"` + mensagem genérica |
| T-QR-PUB-10 | KMS_qr_secret rotacionado | Hashes emitidos antes continuam válidos (resolução consulta tabela) |

Cobertura ≥90% no módulo de QR. Suite roda em CI a cada commit que toca `src/infrastructure/equipamentos/qr_*` ou `src/application/equipamentos/qr_*`.

---

## 6. Evolução / governança

- Mudança na tabela da seção 2 → exige ADR + atualização desta allowlist + bump CHANGELOG.
- Adicionar campo novo a equipamento → revisar tabela: por default cai em "NÃO" em B/C, exceto se for dado público intrínseco (fabricante/modelo).
- Subscritor cyber pode pedir hardening adicional → entrar como linha em `docs/governanca/controles-compensatorios-codigo-ia.md`.

---

## 7. Referências

- `REGRAS-INEGOCIAVEIS.md` — INV-051 (token opaco HMAC), INV-AUTHZ-001 (decisão sempre via porta), INV-035 (precedente — cert público), INV-013 (log de visualização PII)
- `docs/conformidade/comum/lgpd-rat.md` — RAT-EQP-FOTO, RAT-04 (cert)
- `docs/conformidade/comum/dpa-modelo.md` — cláusula D4 (QR público)
- `docs/adr/0012-autorizacao-unificada.md` — porta AuthorizationProvider
- `docs/adr/0018-scanner-qr-pwa.md` — PWA scanner reusa este endpoint
- Pareceres subagentes em `docs/dominios/suporte-plataforma/modulos/equipamentos/revisoes/PRD-{tech-lead,advogado,corretora}.md`
