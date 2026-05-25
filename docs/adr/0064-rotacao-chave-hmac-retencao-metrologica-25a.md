---
adr: 0064
titulo: Rotação anual de chave HMAC com histórico em KMS Multi-Region — preservar verificabilidade WORM metrológico 25a
status: aceito
data: 2026-05-25
aceito-em: 2026-05-25 (saneamento pré-Marco 4 — decisão Roldão)
proposto-por: agente (saneamento pré-Marco 4 — GATE-CAL-HMAC-RETENCAO)
revisado-por: tech-lead-saas-regulado + consultor-rbc-iso17025 (revisão técnica diferida pós-aceite — não bloqueante)
bloqueia-fase: Wave A Marco 4 (`calibracao`) — sem isso, modelo de domínio ambíguo na retenção de hashes em `EventoDeCalibracao`, `Leitura`, `MedicaoControle`, `PadraoUsado`
depende-de: ADR-0002 (multi-tenancy + RLS), ADR-0007 (camada domínio), ADR-0021 (anonimização vs retenção), ADR-0029 (canonicalização texto probatório)
---

# ADR-0064 — Rotação anual de chave HMAC com histórico em KMS Multi-Region (retenção 25a)

## Contexto

O projeto usa HMAC-SHA256 em vários pontos críticos:

- `EventoDeOS.evento_hash` (Marco 3 — INV-OS-AUD-001)
- `EventoDeCalibracao.evento_hash` (Marco 4 — INV-CAL-AUD-001)
- `Leitura.executor_id_hash` (TEMA-C.12 — HMAC tenant — masking PII em eventos)
- `Calibracao.motivo_cancelamento_hash` (idem)
- `MedicaoControle.executor_id_hash` (idem)
- `PadraoUsado.snapshot_padrao_json.padrao_id_hash` (rastreabilidade cross-tenant proteção)
- QR Code de certificado (Marco 5 — INV-051 / SEC-QR-001 — HMAC anti-mineração)
- QR Code de equipamento (Marco 2 — implementado)
- Cadeia hash-chain de eventos (INV-CAL-AUD-001 — `evento_anterior_hash`)

**Conflito de retenção:**

- **Boa prática criptográfica** (NIST SP 800-57 Part 1 Rev. 5 §5.3.6.1, 6.2.1.4): chave HMAC-SHA256 com vida útil máxima de **2 anos** ("originator usage period") + **1 ano de transição** ("recipient usage period"). Após 3 anos, chave DEVE ser destruída ou arquivada em segurança extrema.
- **Auditoria metrológica ISO 17025 cl. 7.5 + cl. 8.4**: registros técnicos preservados por **25 anos** (matriz de retenção `docs/conformidade/comum/retencao-matriz.md`). Significa que **um hash gerado em 2027 com chave X precisa ser verificável em 2052** — 25 anos depois.
- **CGCRE auditoria de supervisão**: a qualquer momento entre 2027-2052, auditor pode pedir verificação de cadeia hash-chain. Se chave X foi destruída, hash é "tijolo opaco" — auditor presume comprometimento da trilha.

Sem decisão, modelo de domínio M4 fica ambíguo:

- Persistir `evento_hash` cru sem versão = chave Y troca em 2027 e todo hash 2026 vira não-verificável.
- Persistir só sem rotação = chave 25a viola NIST + risco de comprometimento longa-duração.
- Persistir hash + tenant_id mas sem cravar `chave_versao` = não dá pra saber qual chave verificar 10 anos depois.

## Decisão

**Adotar rotação anual de chave HMAC com histórico preservado em AWS KMS Multi-Region (sa-east-1 + us-east-1) por 25 anos, com versão da chave embutida em cada hash gerado.**

### Mecânica

1. **Chave ativa por tenant**: `HMAC_KEY_<tenant_id>_v<NN>` armazenada em AWS KMS Multi-Region (chave dedicada — não a `BIOMETRIA_KEY_*`).
2. **Rotação**: chave nova `v(N+1)` gerada anualmente em data fixa (01/jan UTC por tenant). Cron Wave A → procrastinate job `rotacionar_chaves_hmac_tenant`.
3. **Histórico imutável**: chave antiga `vN` **NÃO** é destruída — é movida para estado `DISABLED_BUT_RETAINED` no KMS (políticas IAM impedem deleção até 2052+25=2077). Custo KMS: ~US$ 1/mês por chave × 25 chaves × N tenants — aceito.
4. **Hash carrega versão**: formato canônico `v<NN>$<base64(hmac_sha256(payload))>` (separador `$` — não-ambíguo). Verificação: parse versão, busca `HMAC_KEY_<tenant>_v<NN>` em KMS, valida.
5. **Cross-region**: KMS Multi-Region Key replica `sa-east-1 → us-east-1` automaticamente — verificação funciona em DR (us-east-1) mesmo se sa-east-1 cair.

### Pattern Python (referência — implementação Marco 4 P3)

```python
# src/infrastructure/crypto/hmac_versionado.py
import boto3
from base64 import b64encode, b64decode
import hmac
import hashlib

def hmac_versionado_gerar(tenant_id: str, payload: bytes) -> str:
    versao_ativa = obter_versao_chave_ativa(tenant_id)  # cache + KMS describe
    chave = kms_get_chave_simetrica(f"HMAC_KEY_{tenant_id}_v{versao_ativa:02d}")
    digest = hmac.new(chave, payload, hashlib.sha256).digest()
    return f"v{versao_ativa:02d}${b64encode(digest).decode()}"

def hmac_versionado_verificar(tenant_id: str, payload: bytes, hash_versionado: str) -> bool:
    versao_str, hash_b64 = hash_versionado.split("$", 1)
    versao = int(versao_str.lstrip("v"))
    chave = kms_get_chave_historica(f"HMAC_KEY_{tenant_id}_v{versao:02d}")  # KMS lista DISABLED_BUT_RETAINED
    digest_esperado = hmac.new(chave, payload, hashlib.sha256).digest()
    return hmac.compare_digest(b64decode(hash_b64), digest_esperado)
```

### Invariantes próprias (`INV-HMAC-*`)

- **INV-HMAC-001**: TODO hash HMAC persistido em entidade WORM (`EventoDeOS`, `EventoDeCalibracao`, `Leitura`, `MedicaoControle`, `PadraoUsado.padrao_id_hash`, QR cert, QR equipamento) usa formato canônico `v<NN>$<base64>`. Verificável por hook `hmac-versao-formato-check.sh`.
- **INV-HMAC-002**: chave em estado `DISABLED_BUT_RETAINED` no KMS NUNCA pode ser deletada antes de **ano corrente + 25**. Política IAM `kms:ScheduleKeyDeletion` proibida em chaves `HMAC_KEY_*`. Verificável por drill `validar_kms_retencao_hmac` Wave A.
- **INV-HMAC-003**: rotação anual deve criar nova chave **antes** de desabilitar a anterior (janela 30 dias overlap). Job procrastinate falha-rápido se KMS rejeita create.
- **INV-HMAC-004**: chave Multi-Region replica obrigatoriamente entre `sa-east-1` e `us-east-1`. Hook `kms-multi-region-check.sh` valida policy.
- **INV-HMAC-005**: tentativa de verificar hash com chave inexistente no KMS retorna `HmacChaveVersaoInexistente` (não-silencioso). Auditoria pega tentativa de corrupção da trilha.

### Cenários edge

- **Tenant deletado (LGPD esquecimento estrutural)**: chaves `HMAC_KEY_<tenant_id>_v*` permanecem em KMS por 25a (Zona B — ADR-0021 anonimização-em-lugar). PII original já está em estado eliminado/anonimizado; hash continua verificável como "selo cripto da existência do registro".
- **Reemissão de certificado 10 anos depois**: gera novo hash com chave atual `vN+10`; hash original `vN` permanece no histórico de auditoria com `causation_id` apontando ao novo.
- **Comprometimento de chave atual**: `kms:Disable` imediato + nova chave `vN+1` gerada + evento `Chave.Comprometida` publicado + audit alerta. Hashes históricos `vN-K..vN-1` permanecem verificáveis (chaves DISABLED_BUT_RETAINED separadas).
- **Mudança de algoritmo (SHA-256 → SHA-3 ou pós-quântico)**: formato `v<NN>` admite extensão `v01s256` vs `v01s3` se necessário em ADR futura — não força ADR agora.

## Consequências

### Positivas

- ISO 17025 cl. 8.4 (retenção 25a) preservada — auditor CGCRE verifica cadeia hash em qualquer ano.
- NIST SP 800-57 best-practice cumprida (rotação anual).
- Comprometimento de chave atual NÃO compromete histórico (chaves antigas independentes em KMS).
- DR cross-region: us-east-1 verifica hash gerado em sa-east-1.
- Pattern uniforme para Marco 4 + Marco 5 + retrofit Marco 2 (QR equipamento) + Marco 3 (eventos OS).

### Negativas

- **Custo KMS**: ~US$ 1/mês × 25 anos × N tenants × 2 regiões = ~US$ 50/mês por tenant em ano 25 (1 chave ativa + 24 históricas). Custo aceitável (cliente regulado paga >R$ 500/mês).
- **Complexidade de leitura**: cada verificação requer parse + KMS lookup (cache local mitiga — chaves históricas raramente mudam).
- **Migration retrofit**: hashes pré-ADR-0064 (Marco 2 QR equipamento + Marco 3 EventoDeOS) precisam ser **convertidos formato canônico** (script de migração) OU ADR aceita período de transição onde hooks aceitam ambos formatos com warning.

### Riscos mitigados

- **R-METRO-RETENCAO** (cadeia hash quebrada após rotação) — formato carrega versão.
- **R-CRIPTO-LONGA-DURACAO** (chave 25a comprometida) — rotação anual + histórico isolado.
- **R-DR-CROSS-REGION** (hash gerado em SP não verifica em VA) — Multi-Region Key.

## Plano de implementação

1. **Marco 4 P3** (esta ADR base): `src/infrastructure/crypto/hmac_versionado.py` + helpers `hmac_versionado_gerar/verificar` + KMS client Multi-Region (mock em test, real em integration).
2. **Marco 4 P3**: 5 INVs cravados em `REGRAS-INEGOCIAVEIS.md` §INV-HMAC-*.
3. **Marco 4 P3**: cron procrastinate `rotacionar_chaves_hmac_tenant` (executa 01/jan UTC anualmente).
4. **Marco 4 P9** (hooks): `hmac-versao-formato-check.sh` + `kms-multi-region-check.sh`.
5. **Wave A operacional**: drill `validar_kms_retencao_hmac` (lista chaves DISABLED_BUT_RETAINED por tenant + verifica IAM policy).
6. **Retrofit Marco 2 + Marco 3**: script de migração `python manage.py migrar_hashes_formato_canonico` — Wave A, **não bloqueia Marco 4**. Hook aceita ambos formatos com warning durante janela 90 dias.
7. **Aceite formal pelos 2 subagentes** (tech-lead-saas-regulado + consultor-rbc-iso17025) — diferido, **não bloqueante** pra arrancar Marco 4 P1.

## Non-goals desta ADR

- NÃO trata chave assimétrica (A3 / ICP-Brasil) — ADR-0009 + ADR-0048 cobrem.
- NÃO trata chave de cifragem de PII (`BIOMETRIA_KEY_*`, `PII_KEY_*`) — política específica em `docs/seguranca/`.
- NÃO trata rotação manual emergencial por incidente — runbook operacional Wave A.
- NÃO trata custo de KMS em tenant que cancele em 2030 (chaves vão pra 2055) — política de billing tenant-cancelado em ADR futura.

## GATEs Wave A vinculados

- **GATE-CAL-HMAC-RETENCAO** — fechado por esta ADR (substituído por GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK).
- **GATE-HMAC-RETROFIT-MARCO-2-3** — script migração formato canônico Wave A operacional.
- **GATE-KMS-IAM-LOCK** — IAM policy bloqueando `kms:ScheduleKeyDeletion` em chaves `HMAC_KEY_*` (Terraform Wave A).
- **GATE-HMAC-DRILL** — drill `validar_kms_retencao_hmac` integrado à suite verificação periódica (Marco 4 P10).
