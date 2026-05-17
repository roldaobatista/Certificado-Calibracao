---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Supply chain — dependências, lockfile, SBOM

> **Pra quê:** controlar o que entra no projeto via dependências (pip, npm, pub.dev, apt). Cada pacote é código de terceiros rodando com mesma permissão da aplicação.

---

## 1. Princípios

1. **Lockfile obrigatório** em toda stack (`poetry.lock`, `package-lock.json`, `pubspec.lock`, `Pipfile.lock`)
2. **Allowlist de registries** — só PyPI oficial, npm oficial, pub.dev oficial
3. **Pin de versão exata** em produção (`==1.2.3`, não `^1.2` nem `~1.2`)
4. **Pacote novo = ADR** — adicionar dep não-trivial exige ADR justificando
5. **SBOM gerada em cada build** (CycloneDX ou SPDX)

---

## 2. Hooks de proteção

| Hook | Trigger | Função |
|------|---------|--------|
| Lockfile check em CI | PR | Verifica que `*.lock` mudou junto com `requirements.txt`/`package.json`/`pubspec.yaml` |
| Dependabot | Diário | Abre PR de atualização de segurança |
| Trivy scan | PR + nightly | Scan de CVE em dependências + container |
| `pip-audit` / `npm audit` / `flutter pub outdated` | PR | Auditoria automática de vulnerabilidades conhecidas |
| Hook "pacote novo = ADR" | PreToolUse(Write\|Edit) em `requirements.txt`/`pyproject.toml`/`package.json`/`pubspec.yaml` | A criar — bloqueia se diff adiciona dependência sem ADR correspondente |

---

## 3. Allowlist de registries

| Registry | Status | Notas |
|----------|--------|-------|
| PyPI oficial (`pypi.org`) | ✅ | Single source pra Python |
| npm oficial (`registry.npmjs.org`) | ✅ | Single source pra JS/TS (se vier no futuro) |
| pub.dev oficial | ✅ | Single source pra Dart/Flutter |
| apt/Debian oficial | ✅ | Pacotes do sistema na imagem Docker |
| GitHub Container Registry | ✅ | Imagens base pinadas por digest, não `latest` |
| Outros (private registry, mirror) | ❌ | Vetado — exige ADR |

---

## 4. Pin de versão e digest

### Python (Poetry)
```toml
[tool.poetry.dependencies]
django = "5.0.6"        # versão exata
psycopg = "3.1.18"
```

### Flutter
```yaml
dependencies:
  flutter:
    sdk: flutter
  drift: 2.20.0           # versão exata
```

### Docker
```dockerfile
FROM python:3.12.4-slim@sha256:<digest>   # pin por digest, não tag
```

---

## 5. SBOM (Software Bill of Materials)

- Geração automática em cada build de produção (CI step)
- Formato: CycloneDX JSON
- Armazenamento: artifact GitHub Actions + Backblaze B2 (retenção 5 anos)
- Conteúdo: nome, versão, hash, origem (PyPI/npm/pub.dev), license, CVEs conhecidas
- Revisão: Auditor de Segurança bate SBOM contra advisory database em cada PR

Exemplo de step (a integrar em workflow quando código existir):
```yaml
- name: SBOM CycloneDX
  run: |
    pip install cyclonedx-bom
    cyclonedx-py -o sbom.json
```

---

## 6. Pacote novo = ADR

Toda dependência **nova** (não atualização de versão) exige ADR `docs/adr/NNNN-dep-<nome>.md` com:

1. **Necessidade:** por que adicionar
2. **Alternativas consideradas:** outras libs ou implementação caseira
3. **Licença:** MIT/Apache/BSD ok; GPL/AGPL exige análise (subagent `advogado-saas-regulado`)
4. **Manutenção:** última release, número de contributors, último commit
5. **Vulnerabilidades:** scan inicial (Snyk/Trivy/OSV)
6. **Tamanho:** transitive deps adicionadas
7. **Aprovação:** Roldão + Auditor de Segurança

Atualização de versão minor/patch dispensa ADR — só revisão de changelog + scan.
Atualização major exige ADR (breaking changes).

---

## 7. Crítica de incidentes conhecidos

### event-stream (2018, npm)
Pacote popular foi vendido pra mantenedor malicioso que adicionou backdoor pra roubar Bitcoin.
**Lição:** scan de mudança de mantenedor + pin de versão exata + reviewar updates.

### colors.js (2022, npm)
Mantenedor sabotou a própria lib em protesto.
**Lição:** pin de versão exata + lockfile + não usar `latest`.

### log4shell (2021, Java)
RCE via deserialização em pacote universalmente usado.
**Lição:** SBOM + scan automático + path de update rápido (não esperar Dependabot).

### PyTorch dependency confusion (2023)
Atacante registrou pacote homônimo em PyPI público pra atacar pipelines que misturavam público + privado.
**Lição:** allowlist de registries + pin por hash.

---

## 8. Resposta a CVE crítico

| Severidade | SLA fix |
|------------|---------|
| Critical (CVSS 9.0+) | 24h pra patch em produção; comunicar tenants em 4h |
| High (7.0-8.9) | 7 dias |
| Medium (4.0-6.9) | 30 dias |
| Low | próximo ciclo |

Workflow de resposta:
1. Detecção (Dependabot/Trivy/CVE feed)
2. Avaliar exposição real (dependência usada vs decorativa)
3. Aplicar patch ou mitigação (downgrade temporário, feature flag)
4. PR + auditor de segurança
5. Deploy
6. Postmortem se for crítico

---

## 9. Auditoria

- Mensal: Auditor de Segurança revisa SBOM agregada
- Trimestral: drill — Roldão tenta adicionar pacote suspeito; hook + auditor pegam?
- Anual: revisar política inteira (este doc)

---

## 10. Referências

- `REGRAS-INEGOCIAVEIS.md` — SEC-001 (proibido segredo commitado)
- `docs/conformidade/comum/seguranca-dados.md` — política de segurança geral
- `docs/seguranca/mcp-policy.md` — MCP servers são casos especiais
- `docs/governanca/auditor-seguranca-prompt.md`
