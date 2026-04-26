# Finding — Endpoints operacionais permitem `?scenario=` sem autenticação em produção

## Status

Mitigado em 2026-04-26. `?scenario=` bloqueado em produção via `ALLOW_SCENARIO_ROUTES=false` (default); testes mantidos com `true` em teste.

## Contexto

Endpoints operacionais (`GET /emission/workspace`, `GET /emission/review-signature`, `GET /emission/signature-queue` e outros) aceitam `?scenario=<nome>` e retornam payload canônico/cenário estático, contornando ou relaxando os guards de autenticação e persistência usados no fluxo real.

Isso é aceitável para desenvolvimento, demo e testes de contrato, mas representa um bypass se estiver disponível em ambientes produtivos.

## Impacto

- Leak de estrutura interna e cenários de teste em produção.
- Possível bypass de autenticação se o endpoint operacional não revalidar sessão quando `scenario` está presente.
- Confusão operacional: usuário pode achar que está vendo dados reais quando são cenários sintéticos.

## Correção recomendada

1. Remover `?scenario=` de endpoints operacionais em produção, ou mover para rota separada prefixada (`/demo/`, `/eval/`).
2. Se necessário manter, proteger com feature flag (`ALLOW_SCENARIO=false` por padrão em prod) e requerer role `admin`/`qa`.
3. Garantir que endpoints de emissão real (POST/PUT) nunca aceitem `scenario`.
4. Documentar claramente no contrato quais rotas suportam modo cenário e em que ambientes.

## Rastreamento

- Área crítica: `apps/api/src/interfaces/http/emission-workspace.ts`, `apps/api/src/interfaces/http/review-signature.ts`, `apps/api/src/interfaces/http/signature-queue.ts`
- Requisito PRD: fluxo operacional central V3+
