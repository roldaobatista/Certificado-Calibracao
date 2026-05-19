---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
frente: FA-A1 + FA-M2
revisor: tech-lead-saas-regulado + advogado-saas-regulado
veredito: APROVA COM CORREÇÕES/RESSALVAS (absorvidas — ver §Correções absorvidas)
---

# FA-A1 + FA-M2 — Design: PII_HASH_KEY versionada + hardening de prod

> Código sensível: segurança (gestão de chave criptográfica) + LGPD/ANPD (rastreabilidade retroativa de quem viu PII). Estado real verificado (Regra #0).

## Estado real verificado

- `base.py:43-48`: `PII_HASH_KEY` = env `PII_HASH_KEY` se setada; **senão deriva** `sha256("afere-pii-hmac-v1:"+SECRET_KEY)`. Rotacionar `SECRET_KEY` (boa prática de segurança) **invalida todos os hashes de PII retroativos** → impossível responder ANPD "quem viu CPF X em data Y" (FA-A1, ALTO).
- `audit/services.py:hashear_pii_com_salt_tenant`: `hmac.new(PII_HASH_KEY, f"{tenant_id}:{valor}", sha256).hexdigest()` — **sem prefixo de versão**. Não há como saber com qual chave um hash foi gerado.
- `prod.py`: placeholder vazio. Hardening (HSTS, cookies seguros, SSL redirect) só comentado. Sem gate que barre deploy com `PII_HASH_KEY`/`SECRET_KEY` default (FA-M2, MÉDIO).
- **Não há dado de produção** (memória `project_deploy_so_quando_roldao_quiser`: sem deploy, dogfooding-only; `test_afere` é efêmero). Logo **não existe hash legado de PII em prod a preservar** → não precisa de ponte de compatibilidade v0; troca limpa pra versionado.

## Decisão de design

### FA-A1 — chave dedicada + versionamento + rotação sem perder histórico

1. `base.py`:
   - `PII_HASH_KEY_ID = env("PII_HASH_KEY_ID", default="v1")` — id da chave ATIVA.
   - `PII_HASH_KEY` (env, segredo cru da chave ativa).
   - `PII_HASH_KEYS_RETIRED = env("PII_HASH_KEYS_RETIRED", default="")` formato `"v0:segredo0,v(-1):segredoX"` — chaves aposentadas, só pra **verificar** hashes antigos após rotação.
   - Registry: `PII_HASH_KEYS: dict[str, bytes]` = `{PII_HASH_KEY_ID: <ativa>, **<retired parseadas>}`.
   - Fallback derivado de SECRET_KEY **só fora de prod** (dev/test): mantém DX. prod.py proíbe (item FA-M2).
2. `audit/services.py`:
   - `hashear_pii_com_salt_tenant(...)` passa a retornar `f"{settings.PII_HASH_KEY_ID}:{hexdigest}"` (prefixo de versão) usando a chave ativa.
   - Novo `verificar_pii_hash(valor, tenant_id, hash_armazenado) -> bool`: faz split do prefixo `vN:hex`; resolve a chave em `PII_HASH_KEYS` (ativa OU aposentada); recomputa; `hmac.compare_digest` (tempo constante). **Versão desconhecida → raise** (loud: sem a chave aposentada não há como afirmar à ANPD; silenciar seria mascarar).
   - Sem ponte v0 (não há dado legado — ver estado real). Hash sem prefixo → tratado como entrada inválida (raise), não "legado silencioso".
3. Rotação (runbook, não código agora): gerar `PII_HASH_KEY` nova, mover a anterior pra `PII_HASH_KEYS_RETIRED`, subir `PII_HASH_KEY_ID`. Hashes novos saem `vN+1:`; antigos `vN:` continuam verificáveis enquanto a chave aposentada estiver no registry.

### FA-M2 — hardening + gate de deploy em prod.py

`prod.py` (herda base):
- **Hard fail (`ImproperlyConfigured`)** se `env("PII_HASH_KEY", default="")` vazio (sem derivação de SECRET_KEY em prod).
- **Hard fail** se `SECRET_KEY` == default inseguro de dev (detectar pelo valor do `.env` de dev).
- Ativar: `SECURE_SSL_REDIRECT=True`; `SECURE_HSTS_SECONDS=31536000` + `INCLUDE_SUBDOMAINS` + `PRELOAD`; `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE=True`; `SECURE_CONTENT_TYPE_NOSNIFF=True`; `X_FRAME_OPTIONS="DENY"`; `SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")` (atrás do proxy Hostinger). `DEBUG=False` (já).
- CSP fica fora do escopo (depende de inventário de assets — Wave A UI). Declarar non-goal.

## Testes obrigatórios (happy + UNHAPPY)

- `verificar_pii_hash` round-trip com chave ativa = True; payload adulterado = False.
- **Rotação**: hash gerado com `v1` ainda verifica True depois que ativa vira `v2` (v1 em RETIRED). Prova o objetivo FA-A1.
- Versão desconhecida (`v9:...` sem chave) → raise (UNHAPPY explícito).
- `hashear_pii_com_salt_tenant` retorna string com prefixo `v1:`.
- Settings prod: sem `PII_HASH_KEY` → `ImproperlyConfigured` (UNHAPPY); com chave → importa e flags de hardening setadas.
- `hmac.compare_digest` usado (não `==`) — regressão de tempo-constante.

## Não-objetivos (princípio 4)

- NÃO migrar hashes legados (não existem — sem prod data). Sem ponte v0.
- NÃO implementar rotação automática de chave (runbook manual; automação é pós-MVP).
- NÃO CSP nesta frente (depende de inventário de assets Wave A).
- NÃO mexer em KMS/AWS (ADR-0001 — chave de PII é segredo de app, não material KMS nesta fase).

## Pontos para os revisores

- (T1 tech-lead) Registry `dict[str,bytes]` em settings + parse de env `"v0:seg0,..."` — formato robusto? Risco de vazar segredo em log/repr de settings?
- (T2 tech-lead) Detectar SECRET_KEY default inseguro por comparação de valor é frágil? Alternativa melhor (ex: env explícita `DJANGO_ENV=prod` exige conjunto mínimo)?
- (A1 advogado) Sem ponte de hash legado é defensável perante ANPD, dado que NÃO há dado pessoal em produção ainda (dogfooding-only, sem deploy)? Há obrigação de retenção que isso viole?
- (A2 advogado) `verificar_pii_hash` raise em versão desconhecida (em vez de False) — correto pro dever de prestar contas (não afirmar falsamente "não casou")?
- (A3 advogado) Runbook de rotação manual com `PII_HASH_KEYS_RETIRED` atende o princípio de prestação de contas / rastreabilidade LGPD art. 37?

## Correções absorvidas (review tech-lead + advogado 2026-05-18)

Tech-lead **APROVA COM CORREÇÕES**; advogado **APROVA COM RESSALVAS**. Todas absorvidas antes do implement:

- **(T1 BLOQUEANTE)** `dict` de bytes em settings vaza segredo via `manage.py diffsettings` (NÃO redige valores) e via error report 500. Conserto: registry encapsulado em classe `_RegistroChavesPII` com `__repr__`/`__str__` redatados (`<RegistroChavesPII: ids=[v1,v0] (redacted)>`). Settings expõe **só** o objeto `PII_HASH_KEY_REGISTRO` — NÃO expõe `PII_HASH_KEY` como bytes crus no namespace de settings. Acesso aos bytes só via método explícito `.chave_ativa()`/`.chave(id)`. Teste de regressão anti-vazamento: segredo NÃO aparece em `str(get_safe_settings())` nem na saída de `diffsettings`.
- **(T2 exigido)** NÃO detectar SECRET_KEY default por comparação de valor (`.env` nem é versionado). Inverter: `prod.py` exige presença + não-vazio + piso de entropia — `DJANGO_SECRET_KEY` ≥ 50 chars, `PII_HASH_KEY` ≥ 32 chars, `PII_HASH_KEY_ID`, `DJANGO_ALLOWED_HOSTS` não-vazio → senão `ImproperlyConfigured`. `PII_HASH_KEYS_RETIRED` malformado (`"v0"` sem `:`, `"v0:"`, vírgula dupla) → `ImproperlyConfigured` no import, nunca silêncio.
- **(T3 anotado)** resolução de chave acontece ANTES e FORA da comparação sensível; `hmac.compare_digest` sobre hexdigest completo de mesmo tamanho; nenhum `==` no caminho. Prefixo `vN` é identificador público (viaja no hash) — early-return em versão desconhecida não vaza material.
- **(T4 trava de go-live)** "sem ponte v0" depende de banco virgem. Adicionar item de runbook go-live + gate forte: o helper SEMPRE retorna hash prefixado (teste garante) → nenhum hash sem prefixo pode nascer daqui pra frente; e check humano no 1º deploy real confirmando zero `AcessoDadosCliente`/audit com hash sem prefixo. Registrado em §Trava de go-live.
- **(T5 feito)** chamadores de `hashear_pii_com_salt_tenant` mapeados: `views.py` (helpers ip/doc), `job_inadimplencia_alertas.py`, teste US-CLI-003 (compara saída-da-função com saída-da-função → prefixo em ambos, igualdade preservada). `views.py:835` usa `settings.PII_HASH_KEY` cru pra derivar chave de dedup de linha CSV → migra pra `settings.PII_HASH_KEY_REGISTRO.chave_ativa()`. Nenhum match de formato externo não-prefixado.
- **(R2 BLOQUEANTE, advogado)** acrescentar linha à `docs/conformidade/comum/retencao-matriz.md`: chave aposentada `PII_HASH_KEYS_RETIRED` retém ≥ maior prazo de qualquer audit trail que a usou (10 anos, "audit trail paths sensíveis"); descarte só após crypto-shredding de 100% dos hashes gerados sob ela; ação: eliminação.
- **(R1 advogado)** exceção `ChavePIIIndisponivel` com mensagem inequívoca: "versão de chave 'vN' ausente do registry — verificação INCONCLUSIVA, não negativa". Chamador que responde ANPD/titular registra em audit "resposta inconclusiva por chave aposentada indisponível" (este último é responsabilidade do call site de resposta a titular — Wave A; aqui garantimos a exceção correta + mensagem).
- **(R3 advogado)** varredura terminológica: o hash de PII é **pseudonimização com chave de servidor**, NÃO anonimização. Revisar `retencao-matriz.md` (linhas ~73/89/102) — "anonimização por hash ao fim de prazo" só se sustenta combinada com crypto-shredding da chave KMS do tenant; ajustar redação pra não qualificar errado perante ANPD.

## Trava de go-live (T4 — não tratar como pendência de F-A)

Antes do 1º deploy real com PII (autorização Roldão / 1º tenant pago):
1. Confirmar (check humano) zero linha de audit/`AcessoDadosCliente` com hash de PII SEM prefixo `vN:`.
2. `PII_HASH_KEY` dedicada provisionada (não derivada) + `PII_HASH_KEY_ID` setado.
3. Runbook de rotação operacionalizado + linha da matriz de retenção das chaves aposentadas ativa.
Enforced no código: o helper só emite hash prefixado (teste de regressão) → impossível criar hash sem prefixo após esta frente.
