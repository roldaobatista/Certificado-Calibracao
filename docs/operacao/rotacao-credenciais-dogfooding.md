---
owner: roldao
revisado-em: 2026-05-24
status: stable
diataxis: how-to
audiencia: agente
relacionados:
  - docs/operacao/runbook.md
  - docs/operacao/drills/
  - docs/faseamento/F-C1/spec.md
  - REGRAS-INEGOCIAVEIS.md
---

# Rotação de credenciais — procedimento dogfooding

> **F-C1 P4 T-FC1-12** — exercício de procedimento antes do produtivo (F-C3 com KMS MRK).
>
> **Para quê:** ter o playbook exercitado pelo menos 1 vez antes do 1º deploy externo. Quando a rotação produtiva entrar em F-C3 (KMS automático), os passos do procedimento (gerar, substituir, validar, eliminar antigo) já são conhecidos.

---

## 1. Quando rotacionar

Cenário dogfooding (janela atual):

- **Mensal** (recomendado): exercício de procedimento + reduz janela de exposição se a chave vazar sem ser detectada.
- **Imediato** se:
  - Suspeita de vazamento (gitleaks histórico achou — não foi o caso em 2026-05-23, mas o procedimento existe).
  - Computador do Roldão foi comprometido.
  - Pessoa com acesso ao `.env` saiu do projeto (Roldão é único hoje — N/A).

---

## 2. Credenciais que rotacionam

| Chave | Onde fica | Tamanho mínimo | Cobertura |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `.env` | 50 chars | Sessões + CSRF + signing de cookies |
| `PII_HASH_KEY` + `PII_HASH_KEY_ID` | `.env` | 32 chars + ID | HMAC de PII (cliente, RT). Hashes sobrevivem rotação (KEY_ID preservado) |
| `QR_HMAC_KEY` + `QR_HMAC_KEY_ID` | `.env` | 32 chars + ID | HMAC de etiqueta QR (25 anos de vigência — rotacionar com cuidado) |
| `QR_IP_RATELIMIT_SALT` | `.env` | 32 chars | HMAC de IP do rate-limit QR público |
| `ADMIN_ACCESS_HASH_SALT` (F-C1) | `.env` | 32 chars | HMAC de IP + UA em audit `admin_access` |

**Não rotacionar nesta operação:**
- `PII_HASH_KEY_ID` e `QR_HMAC_KEY_ID` mudam só na rotação seguinte com versionamento (preservam hashes antigos).
- Chave HMAC de cada `webhook_destino` (F-C1) — rotação é por destino, segue ciclo da chave externa.

---

## 3. Procedimento passo-a-passo (dogfooding)

### 3.1 Preparar nova chave

Numa sessão do Git Bash, na raiz do projeto:

```bash
# DJANGO_SECRET_KEY (50+ chars)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Chaves HMAC genéricas (32 chars hex)
openssl rand -hex 32
```

Copiar o valor para a área de transferência. **NÃO** salvar em arquivo intermediário.

### 3.2 Backup do `.env` antigo (para diff de auditoria do drill)

```bash
cp .env .env.bkp-pre-rotacao-$(date +%Y%m%d-%H%M%S)
```

Esse backup é **temporário** — eliminado no passo 3.6.

### 3.3 Substituir no `.env`

Abrir `.env` em editor e substituir o valor da chave alvo. Bumpar o `KEY_ID` se aplicável (ex: `PII_HASH_KEY_ID=v2` → `v3`).

### 3.4 Restart do app

```bash
docker compose restart app worker
```

Aguardar `app | Watching for file changes` no log (~5s).

### 3.5 Validação

```bash
# Confirma que app subiu com a nova chave
docker compose exec app poetry run python manage.py check

# Confirma que sessões antigas estão inválidas
# (no navegador: tentar acessar /admin/ — deve forçar re-login)

# Para chave HMAC: confirmar que hash novo difere do antigo com mesmo input
docker compose exec app poetry run python manage.py shell -c "
from src.infrastructure.audit.canonicalizar import hashear_pii
print(hashear_pii('123.456.789-09'))
"
```

### 3.6 Eliminação efetiva (CRÍTICO — LGPD art. 16)

> ⚠️ Sem eliminação efetiva, a "rotação" vira teatro: a chave antiga continua em backup local indefinidamente.

```bash
# 1. shred -u no backup do .env antigo
shred -u .env.bkp-pre-rotacao-*

# 2. Buscar e eliminar cópias em outros lugares
# (lista de verificação manual — adaptar ao computador real)
```

**Checklist manual de eliminação** (rodar mentalmente + arquivar log):

- [ ] `~/.bash_history` (`history -d <linha>` ou `> ~/.bash_history`)
- [ ] `~/.zsh_history` (idem)
- [ ] OneDrive / Google Drive sincronizando o projeto — pausar sync, verificar se há revisão antiga com `.env`
- [ ] Backup local externo (HD, pen-drive) — verificar
- [ ] `.env.example` (NÃO deve ter valor real — só placeholder)
- [ ] Algum subdiretório `tmp/` com `.env` antigo
- [ ] Configurações de IDE (VS Code workspace settings, PyCharm) que possam ter cacheado

### 3.7 Declaração datada (eliminação efetiva)

Criar arquivo em `docs/operacao/drills/rotacao-dogfooding-YYYY-MM-DD.md` com:

```markdown
# Drill rotação dogfooding — YYYY-MM-DD

**Chave rotacionada:** DJANGO_SECRET_KEY (ou outra)
**Operador:** Roldão Batista
**Hora início:** HH:MM
**Hora fim:** HH:MM

## Eliminação efetiva (LGPD art. 16)

Em <data>, eu, Roldão Batista, declaro que a chave anterior foi eliminada
dos seguintes locais conhecidos:
- [x] .env atual sobrescrito
- [x] .env.bkp-pre-rotacao-* eliminado via shred -u
- [x] ~/.bash_history limpo
- [x] OneDrive sync verificado — sem cópia antiga
- [x] Backup local externo (HD): verificado, sem cópia
- [ ] (item específico se aplicável)

Não há cópia ativa da chave anterior em meu conhecimento.

## Validação

- [x] docker compose restart app worker — OK
- [x] manage.py check — 0 issues
- [x] Sessão admin antiga rejeitada (re-login forçado)
- [x] Hash HMAC com chave nova difere do antigo (se aplicável)

## Próxima rotação prevista: YYYY-MM-DD (+30d)
```

Esse arquivo é committado em git (rastreável + auditável).

---

## 4. Mapeamento procedimento manual → KMS produtivo (preparação F-C3)

Em F-C3, a rotação vira automática via AWS KMS MRK. O mapeamento 1:1:

| Passo dogfooding (acima) | Equivalente KMS F-C3 |
|---|---|
| 3.1 gerar nova chave | `aws kms create-key --multi-region` OU `aws kms rotate-key-on-demand --key-id <id>` |
| 3.2 backup `.env` antigo | n/a — versionamento automático do KMS |
| 3.3 substituir no `.env` | Atualizar `KMS_KEY_ID` em Secrets Manager; app lê via IAM role |
| 3.4 restart app | rolling deploy via ECS/Kubernetes (sem downtime) |
| 3.5 validação | dashboards SLO mostram zero erros pós-deploy + sanity check em endpoint protegido |
| 3.6 eliminação efetiva | `aws kms schedule-key-deletion --key-id <antiga> --pending-window-in-days 30` (janela mínima legal) |
| 3.7 declaração datada | Audit log automático do KMS + entrada em `audit_trail.kms_rotation` |

**Quem implementa esse mapeamento em código:** F-C3 T-FC3-KMS-*. **Quem aprova rotação produtiva:** Roldão + DPO (LGPD art. 41 — designação em ADR-0061).

---

## 5. Riscos e mitigações

| Risco | Mitigação dogfooding | Mitigação produtiva (F-C3) |
|---|---|---|
| Chave antiga em backup esquecido | Checklist §3.6 + declaração datada | KMS controla versionamento; sem cópia humana |
| Rotação derruba sessões ativas | Aceito (é dogfooding — Roldão sabe re-logar) | Rolling deploy + sessões re-emitidas com nova chave em background |
| Esquecer de rotar `KEY_ID` em chaves HMAC | Validação §3.5 (hash novo ≠ antigo) | Política KMS exige `KEY_ID` derivado da versão |
| Drill arquivado fica gigante | Arquivo curto por drill (template §3.7) | Audit log estruturado JSON com retenção 25a (ISO 17025) |

---

## 6. Quem revisa este procedimento

- Drill mensal: `auditor-seguranca` revisa o log arquivado (subagente).
- Política de rotação (frequência mínima, chaves cobertas): revisão semestral por `tech-lead-saas-regulado`.
- Antes do 1º tenant externo pago: confirmação por advogado humano licenciado de que a declaração datada é defensável em incidente ANPD.

---

## 7. Drill de aceitação F-C1

Para a F-C1 fechar P4 com aceitação de Roldão, o **primeiro drill** deve ser arquivado em:

`docs/operacao/drills/rotacao-dogfooding-2026-MM-DD.md`

Com o template do §3.7 preenchido. Esse arquivo é AC binário do T-FC1-12.
