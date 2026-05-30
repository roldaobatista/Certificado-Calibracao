---
owner: <SecurityOwner>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 280
proposito: política de aceitação, manutenção e auditoria contínua de dependências de terceiros — licenças, pinning, SBOM, scan de CVE, re-auditoria periódica
---

<!--
template: dependency-policy.template.md
uso: copiar para docs/segurança/dependency-policy.md.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
-->

# Política de Dependências — Aferê Prumo

> **Documento CONDICIONAL.** Aplica-se a projeto regulado, que trate dado pessoal ou que distribua software com dependencias de terceiros. Se o produto nao usa pacotes externos (raro) ou nao se enquadra, **nao preencha** — registre o motivo em `docs/nao-aplica.md`.

> **Dependencia** = qualquer pacote/biblioteca de terceiros que o projeto importa. Cada dep e codigo executando dentro do nosso processo com nossos privilegios. Trata-se como codigo nosso para fins de seguranca.

## 1. Criterios de aceitacao para dep nova

Toda dependencia nova passa por estes filtros **antes** do PR ser aprovado:

| Criterio | Limite minimo | Como verificar |
|---|---|---|
| Downloads recentes | >= 1.000/semana (npm/PyPI) | pagina do pacote no registry |
| Manutencao ativa | commit nos ultimos **6 meses** | repositorio upstream |
| Issues abertas vs fechadas | razao saudavel (nao 500 abertas e zero resposta) | repo upstream |
| Numero de mantenedores | >= 2 quando possivel (bus factor) | repo upstream |
| Licenca | dentro do allowlist (ver §2) | arquivo LICENSE no pacote |
| Tem dep transitiva exotica? | revisar a arvore | `npm ls`, `pip-deptree`, etc. |
| Mantenedor tem 2FA na conta? | sim (npm exibe selo) | registry |
| Existe alternativa na stdlib? | se sim, preferir stdlib | analise pelo revisor |

Reprovacao em **qualquer** criterio exige justificativa documentada no PR.

## 2. Licencas

### 2.1 Allowlist (uso livre)

- MIT
- BSD-2-Clause, BSD-3-Clause
- Apache-2.0
- ISC
- MPL-2.0 (com cuidado em modificacoes)
- Unlicense / CC0 / 0BSD

### 2.2 Denylist (proibidas sem aprovacao juridica)

- GPL-2.0, GPL-3.0, AGPL-3.0 (copyleft forte — risco de contaminar codigo proprietario)
- SSPL (Server Side Public License)
- BSL (Business Source License) sem clausula clara
- "Commons Clause" anexada a licenca permissiva (deixa de ser open source)
- Licenca proprietaria sem contrato assinado
- Pacote **sem** arquivo de licenca

Excecoes exigem aprovacao do `<owner-juridico>` + ADR.

## 3. Pinning e lockfile

- **Lockfile commitado obrigatorio**: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Cargo.lock`, `go.sum`, conforme o ecossistema.
- Versoes pinadas com **igualdade exata** em deps diretas em producao (`1.2.3`, nao `^1.2.3`).
- Em deps de desenvolvimento, faixas amplas (`^`) sao aceitas.
- Lockfile e fonte de verdade: CI quebra se `npm ci` (ou equivalente) detectar drift.

## 4. Idade maxima e atualizacao

| Metrica | Limite | Acao |
|---|---|---|
| Dep direta sem atualizar ha **18 meses** | atingiu | abrir issue de "deprecacao automatica" — substituir ou justificar |
| Atras em mais de 1 major | atingiu | issue de modernizacao com prazo de 90 dias |
| CVE conhecido sem fix disponivel | imediato | mitigar (config, isolar, remover) em 7 dias corridos |
| CVE com fix disponivel CRITICO | imediato | atualizar em 24h |
| CVE com fix disponivel ALTO | imediato | atualizar em 7 dias |

**Rotacao de lockfile**: regenerada e revisada **mensalmente** (ou a cada release minor — o que vier primeiro).

## 5. SBOM (Software Bill of Materials)

> **SBOM** = lista assinada de tudo que o projeto importa, com versoes e hashes. Permite ao consumidor saber se esta exposto a uma CVE recem-publicada.

- Geracao obrigatoria em **cada release** publicado.
- Ferramenta: **Syft** (ou equivalente) → formato **CycloneDX** (JSON).
- Saida: `dist/sbom.cdx.json`, anexada ao artefato de release.
- Verificacao: a pipeline de release falha se o SBOM nao for gerado.
- SBOM versionado junto com o release (nao no main).

## 6. Scanning de vulnerabilidades

| Camada | Ferramenta | Cadencia |
|---|---|---|
| Atualizacoes automaticas | Dependabot OU Renovate | diaria |
| Audit no CI | `npm audit` / `pip-audit` / `cargo audit` / equivalente | a cada PR |
| Scan de SBOM | Grype (ou Trivy) contra o SBOM gerado | a cada release |
| Auditor proprio | `auditor-dependencias` (subagente) | semanal |

Build quebra em CVE CRITICO. Build avisa (nao quebra) em CVE ALTO sem fix ainda disponivel — issue auto-aberta.

## 7. Aprovacao de dependencia nova

Adicionar dep nova exige **2 olhos**:

- Autor do PR adiciona a dep + justifica no corpo do PR (problema que resolve, alternativas avaliadas, criterios de §1 marcados).
- Revisor verifica criterios + licenca + tamanho da arvore transitiva.
- Em time pequeno (< 3 devs): tech-lead aprova; sem tech-lead, owner do projeto.

Trocar versao **major** segue o mesmo rito (e breaking change potencial).

## 8. Typosquatting e supply chain

- **Typosquatting check**: nome do pacote conferido contra o esperado antes do `install`. Sufixos comuns de ataque: `-utils`, `-helpers`, `-core`, `-js` adicionados a nomes populares.
- **Confirmar autor**: para deps importantes, conferir que o publisher corresponde ao repo upstream (npm exibe).
- **Hash pinning**: quando o ecossistema suporta (Go modules, pip com `--require-hashes`), usar.
- **Mirror interno**: deps importantes espelhadas internamente, build nao depende do registry publico estar online.
- **Frozen install em prod**: `npm ci`, `pip install --no-deps -r requirements-frozen.txt`, etc. Nunca resolve dep no deploy.

## 9. Dependencias transitivas

Toda dep direta arrasta uma arvore. Politica:

- Auditar a arvore completa periodicamente (`npm ls --all`, `cargo tree`, equivalente).
- CVE em transitiva e tratada com mesma prioridade da direta.
- Se transitiva problematica nao tem fix upstream: aplicar `overrides`/`resolutions`/equivalente + ADR documentando.
- Profundidade exotica (arvore com >300 pacotes para projeto pequeno) e sinal de alerta — revisar deps diretas.

## 10. Remocao de dependencia

Quando dep e removida do projeto:

- Remover do `package.json`/`pyproject.toml`/etc.
- Regerar lockfile.
- Buscar usos remanescentes no codigo (`grep` pelo nome do modulo).
- Atualizar SBOM no proximo release.

## 11. Re-auditoria periódica pós-aceitação

Aceitar uma dep não termina o trabalho. **Re-auditar** acontece em ciclos:

| Ciclo | O que revisar | Quem dispara | Saída |
|---|---|---|---|
| **Mensal** (automático) | Lockfile diff + CVE database refresh. CVE novo em dep existente abre issue. | CI agendado (`security-audit-monthly.yml`) | Issue + label `security/cve` |
| **Trimestral** | Manutenção upstream — dep ainda recebe commit? Issues abertas há > 90 dias sem resposta? Bus factor caiu? | `auditor-dependencias` (subagente) | Relatório em `docs/segurança/auditoria-deps-<YYYY-Q>.md` |
| **Anual** | Re-confirmação completa dos critérios de §1 para todas as deps diretas. Mantenedor mudou? Licença mudou? Substituível por stdlib? | DPO + `<security-owner>` | Revisão do `dependency-policy.md` |
| **Sunset** | Dep marcada como deprecated upstream OU sem release há 18 meses OU bus factor = 1 e mantenedor inativo > 12 meses | Mensal + trimestral combinados | Issue de substituição com prazo 90 dias + ADR justificando se ficar |

Sinais que disparam re-auditoria fora de ciclo:

- Mudança de mantenedor da dep (npm/PyPI mostra "transferred to ...").
- Repo upstream arquivado, deletado ou movido sem aviso.
- Mantenedor pede doação/sponsor em commit (sinal de exaustão — risco de abandono próximo).
- CVE crítico em transitiva ainda sem fix upstream após 30 dias.
- Mudança de licença (a comunidade noticia em GitHub Watch).

## 12. Exceções

Exceções a esta política exigem:

1. ADR em `docs/adr/` com: contexto, alternativas, decisão, prazo de revisão.
2. Aprovação do `<SecurityOwner>`.
3. Issue de acompanhamento com data de re-avaliação.

## 13. Vinculação com

- `SECURITY.md` (politica geral, secao "Gestao de dependencias").
- `threat-model.md` (perfil de atacante supply-chain).
- `INV-SEC-DEPS-*` (invariantes que verificam politica).
- Auditor `auditor-dependencias` (subagente que aplica regras).
- ADRs em `docs/decisoes/` que registram excecoes.
- Pipeline em `.github/workflows/` (jobs de SBOM, audit, scan).

## 14. Checklist de promoção draft → stable

- [ ] Confirmado que o projeto se enquadra (usa deps de terceiros / é regulado); senão, registrar em `docs/nao-aplica.md`.
- [ ] Critérios de aceitação (§1) e allowlist/denylist de licenças (§2) revisados para a stack real do projeto.
- [ ] Lockfile commitado e CI quebra em drift (§3).
- [ ] **Lista de componentes (SBOM) gerada a cada versão publicada** e anexada ao release (§5).
- [ ] Scanning de CVE configurado por PR e por release, com build quebrando em CVE crítico (§6).
- [ ] Rito de aprovação de dep nova (§7) e ciclos de re-auditoria (§11) com responsável definido.
- [ ] Owners (`<SecurityOwner>`, `<owner-juridico>`) preenchidos com nomes reais.
- [ ] Frontmatter `revisado-em` atualizado; `status: stable`.
