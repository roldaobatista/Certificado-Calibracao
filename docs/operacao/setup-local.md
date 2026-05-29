---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: tutorial
audiencia: dono
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
---

# Setup local — como rodar o sistema no seu PC

> **Pra que serve:** durante a Foundation F-A (4–6 semanas) o sistema vai existir **apenas no seu computador**. Sem servidor remoto, sem cliente acessando, sem cobrança de hospedagem. Quando você quiser ver o que foi construído, este documento ensina o passo-a-passo.
>
> **Quando vai mudar:** quando você autorizar deploy a servidor (memória `project_deploy_so_quando_roldao_quiser`), criamos outro documento de setup do servidor.

---

## Pré-requisitos (instalar 1 vez só)

### 1. Docker Desktop
- **O que é:** programa que sobe vários "computadores virtuais pequenos" dentro do seu PC. O sistema roda dentro dele.
- **Onde baixar:** https://www.docker.com/products/docker-desktop/
- **Como confirmar que está OK:** abrir PowerShell e digitar `docker --version`. Tem que aparecer algo tipo `Docker version 26.x.x`.

### 2. Git Bash (já está instalado no seu PC)
- Os comandos abaixo são pra rodar no Git Bash, não no PowerShell. Procure "Git Bash" no menu iniciar.

---

## Passo 1 — Criar o arquivo `.env` (1 vez só)

O sistema lê configuração de um arquivo chamado `.env` na raiz do projeto. Esse arquivo **não é versionado** (fica só no seu PC) porque guarda senhas locais.

Abra o Git Bash, entre na pasta do projeto e rode:

```bash
cd "/c/PROJETOS/Certificado de calibracao"
cp .env.example .env
```

Agora você precisa adicionar **mais 6 variáveis novas** no `.env` (que ainda não estão no `.env.example` porque ele foi escrito antes da F-A). Abra o arquivo `.env` no bloco de notas e cole isto no final:

```
# Adicionado em 2026-05-17 — Foundation F-A
DJANGO_SECRET_KEY=dev-only-secret-do-NOT-use-in-prod-xkF7sNcaZpQ8wR4mY2v
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
POSTGRES_SUPERUSER=postgres
POSTGRES_SUPERUSER_PASSWORD=postgres_dev_change_in_prod
APP_USER_PASSWORD=app_user_dev_change_in_prod
APP_MIGRATOR=app_migrator
APP_MIGRATOR_PASSWORD=app_migrator_dev_change_in_prod
DATABASE_URL=postgres://app_user:app_user_dev_change_in_prod@db:5432/afere
DATABASE_MIGRATOR_URL=postgres://app_migrator:app_migrator_dev_change_in_prod@db:5432/afere
```

> **Por que duas senhas?** A ADR-0002 cravou: o sistema acessa o banco com um usuário sem privilégio de bypass (`app_user`) e migrations rodam com outro (`app_migrator`). Defesa em profundidade — se um agente IA escrever uma migration errada por engano, não corrompe dados de produção. Pra desenvolvimento local, as senhas são genéricas mesmo; em produção mudam.

---

## Passo 2 — Subir o sistema (toda vez que quiser rodar)

```bash
cd "/c/PROJETOS/Certificado de calibracao"
docker compose up
```

**O que esperar na primeira vez:**
- 3 a 8 minutos baixando imagens (PostgreSQL, Python).
- Mensagens como `[init] roles app_user e app_migrator criadas` — é o banco se configurando.
- No final, uma linha tipo `Starting development server at http://0.0.0.0:8000/`.

**A partir da segunda vez** sobe em ~10 segundos.

---

## Passo 3 — Testar se está funcionando

Abra o navegador em:

- http://localhost:8000/healthz/ — deve mostrar `{"status": "ok", "fase": "foundation-f-a"}`
- http://localhost:8000/admin/ — tela de login do Django
- http://localhost:8000/api/docs/ — documentação da API (vazia ainda; endpoints entram em Wave A)

Se as 3 telas carregarem, o esqueleto está de pé. ✅

### Criar o primeiro usuário (1 vez só, pra conseguir entrar no /admin/)

Em outro Git Bash (deixa o `docker compose up` rodando no primeiro):

```bash
cd "/c/PROJETOS/Certificado de calibracao"
docker compose exec app poetry run python manage.py createsuperuser
```

O comando vai pedir:
- **Email:** seu email (vira o login)
- **Password:** uma senha de **no mínimo 12 caracteres**
- **Password (de novo):** confirma

Depois disso, abra http://localhost:8000/admin/ e faça login. Você vai ver 4 grupos de tabelas:
- **Tenants** — clientes do sistema
- **Usuarios** — quem loga (esta tabela já tem você)
- **Auditoria** — trilha imutável (vazia, vai encher com eventos)
- **Feature flags** — liga/desliga funcionalidade por cliente

---

## Passo 4 — Parar o sistema

No terminal onde rodou `docker compose up`, aperte **Ctrl+C**. Espera as mensagens "Stopping..." aparecerem. Em ~10 segundos volta o prompt.

Pra apagar o banco e começar do zero (raríssimo — só se algo corromper):
```bash
docker compose down -v
```
O `-v` apaga o volume com os dados. Sem ele, os dados ficam pra próxima.

---

## Rodar a suite de testes

Em outro Git Bash (deixa o `docker compose up` rodando):

> **Antes de mexer em testes, leia `docs/operacao/testes-armadilhas.md`** — 3 armadilhas já custaram 5h15 num único dia. Nunca use `--create-db` nem `-o addopts=""`.

```bash
cd "/c/PROJETOS/Certificado de calibracao"

# Dia a dia — comando SEGURO (reaproveita o banco, não dropa, não cai em dev)
docker compose exec app poetry run pytest --no-cov --reuse-db

# Só os rápidos (sem isolamento cross-tenant)
docker compose exec app poetry run pytest --no-cov --reuse-db -m "not tenant_isolation and not slow"

# Só fuzzing de isolamento (50 threads x 100 queries)
docker compose exec app poetry run pytest --reuse-db -m "tenant_isolation and slow"

# Suite completa COM cobertura (fim de fase — mais lento)
docker compose exec app poetry run pytest
# Abre depois: reports/coverage/index.html
```

Se tudo passar, sai algo tipo:
```
=== 38 passed, 1 skipped in 12.4s ===
Coverage: 87.5%
```

## Quando algo dá errado

| Sintoma | O que tentar |
|---|---|
| "docker: command not found" | Docker Desktop não está aberto. Abra-o e espera a baleia ficar verde. |
| Aparece "port 5432 already in use" | Você tem outro PostgreSQL rodando no PC. Mudar `POSTGRES_PORT=5433` no `.env`. |
| Aparece "port 8000 already in use" | Algum outro app está usando essa porta. Mudar `DJANGO_PORT=8001` no `.env`. |
| Tela em branco em http://localhost:8000/admin/ | Olhar o terminal — se aparecer erro vermelho, mandar print pro Claude. |
| "no module named django" | A receita não terminou de instalar. Rodar `docker compose down` e `docker compose up --build` (com `--build`). |

Quando aparecer qualquer outro erro, **copie a mensagem inteira e cole numa conversa com o Claude**. Não tente decifrar sozinho — é trabalho do agente.

---

## Próximos marcos

| Marco | O que muda | Como você vai notar |
|---|---|---|
| ~~**Marco 1**~~ (entregue 2026-05-17) | Esqueleto técnico + Docker local | Tela `/admin/` carrega |
| ~~**Marco 2**~~ (entregue 2026-05-17) | 4 tabelas-núcleo criadas | Em `/admin/` aparecem 4 grupos (Tenants, Usuarios, Auditoria, Feature flags) |
| **Marco 3** (em ~2 semanas) | Trava de isolamento entre clientes | Imperceptível na tela — testes provam que cliente A não vê dado de cliente B |
| **Marco 4** (em ~3 semanas) | Trilha de auditoria com hash em cadeia | Toda ação no `/admin/` deixa rastro num registro impossível de adulterar |
| **Marco final** (4–6 semanas) | F-A fechada | Sistema pronto pra começar Foundation F-B (autenticação + perfis) |
