---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
status: stable
diataxis: reference
frente: configuracoes-sistema
tipo: investigacao-regra-0
relacionados:
  - docs/dominios/suporte-plataforma/modulos/configuracoes-sistema/prd.md
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0017-cnpj-alfanumerico.md
---

# T-CFG-000 — Investigação regra #0 da frente `configuracoes-sistema`

> Frente #1 do plano de dependência (`plano-dependencia-sistema.md`): raiz da cadeia
> de preço. Investigação feita ANTES da spec. Inclui correção factual do plano.

## 1. Estado

- **Código:** greenfield total (`src/{domain,application,infrastructure}/configuracoes_sistema/`
  inexistente). Estrutura **achatada** (molde fiscal/licencas — ADR-0072: achatado para
  módulo com múltiplos agregados consumido por todos).
- **Spec:** PRD `docs/dominios/suporte-plataforma/modulos/configuracoes-sistema/prd.md`
  **status: draft** (revisado 2026-05-17). 14 US (US-CFG-001..014), ~80 AC, modelo-de-domínio
  + contratos (api/ui) + glossário (44 termos) existentes. Promover a stable no fechamento.

## 2. Correção factual do plano de dependência (regra #0)

O `plano-dependencia-sistema.md` afirma que o **fiscal contraiu dívida** emitindo documento
numerado sem o dono `SerieDocumento`. **ISSO ESTÁ ERRADO** — verificado no código:
- `fiscal/models.py`: a NFS-e guarda `provider_invoice_id` (número atribuído pelo **BaaS
  PlugNotas/Focus / município**, não pelo Aferê). NFS-e **não é numerada localmente** — a
  numeração é responsabilidade do município/SEFAZ. Logo fiscal **não depende** de SerieDocumento.
- `ordens_servico` e `calibracao` numeram com **sequences próprias** (`os_numero_seq_global`,
  `calibracao_numero_seq_global`; ADR-0056 + INV-OS-NUM/INV-CAL-NUM) — já resolvidas localmente.

**Conclusão:** `SerieDocumento` (US-CFG-002) é **refactor de centralização futuro**, NÃO bloqueio.
O motivo real de `configuracoes-sistema` ser frente #1 permanece válido por OUTRA via: é a casa
de **Imposto + RegimeTributario** (US-CFG-003) que precificação/fiscal/catálogo consomem, e dos
parâmetros do tenant. A justificativa "dívida de numeração" sai; a justificativa "raiz fiscal/
tributária da cadeia de preço" fica. (Emenda a registrar no plano.)

## 3. Anti-retrabalho — o que JÁ tem dono (NÃO reconstruir)

| US-CFG | Tema | Dono existente | Decisão |
|--------|------|----------------|---------|
| US-CFG-004 | RBAC papéis/permissões | módulo `authz` (AuthorizationProvider ADR-0012, ACTION_MAP, seed) construído | **NÃO reconstruir**; CFG no máximo expõe leitura/admin do que authz já faz |
| US-CFG-014 | Feature flags do tenant | módulo `feature_flag` (ADR-0006) construído | **NÃO reconstruir**; CFG só "ativa o liberado no plano" |
| US-CFG-009 | Integrações/credenciais | KMS (SEC-KMS-001) + webhook_out construídos | reusar; só metadados de config |
| US-CFG-008 | Cert A3 + posição | ADR-0009 (Lacuna client-side) | diferir (depende de assinatura) |
| US-CFG-013 | Backup/retenção | matriz `retencao-matriz.md` + B2 | config fina diferida |

## 4. Recorte de NÚCLEO proposto (fatiar — INV-RITUAL-002)

Núcleo = o que destrava a cadeia de preço + cadastro base, sem reconstruir o que tem dono:

1. **`Empresa` + `Filial`** (US-CFG-001) — INV-036 (CNPJ único por tenant, usa VO CNPJ ADR-0017),
   INV-037 (exatamente 1 matriz). Base de cadastro do tenant.
2. **`Imposto` + `RegimeTributario`** (US-CFG-003) — VO/enum + tabela versionada com vigência
   (INV-026 não-retroativo pós-uso). É o que precificação/fiscal precisam.
3. **`SerieDocumento`** (US-CFG-002) — INV-028 (proximo_numero estritamente monótono) +
   emissão atômica `UPDATE ... RETURNING`. Útil para catálogo/orçamento/futuros docs locais
   (não para NFS-e, que é do BaaS). Incluir no núcleo por ser barato e pré-req de orçamento.

**Diferido (pós-núcleo ou Wave B):** workflows/status personalizados (US-CFG-005), campos
obrigatórios (006), modelos PDF (007), A3 (008), notificações (010), regras comerciais (011),
SLA (011), config operacional fina (012), backup/retenção fina (013). RBAC/feature-flag = dono
existente.

## 5. Invariantes do núcleo

INV-028 (série monótona), INV-026 (imposto versionado não-retroativo), INV-036 (CNPJ único),
INV-037 (1 matriz), INV-001/INV-TENANT-001 (RLS), SEC-005 (auditoria config WORM),
ADR-0067 (perfil server-side onde houver gating). Numeração atômica = INV-006.

## 6. Seam de saída (greenfield a jusante — não bloqueia)

Consumidores (`produtos-pecas-servicos` impostos/preço, `estoque` multi-depósito, `precificacao`,
`orcamentos`, emissores de doc local) ainda NÃO existem → seam pronto. Módulos construídos
(fiscal/OS/calibração) seguem com numeração própria; centralização via SerieDocumento é
refactor opcional Wave B (não retrofitar agora).

## 7. Questões para a spec (decisões a cravar em P1/P2 — tech-lead)

- Q1 `SerieDocumento`: só `proximo_numero` + emissão atômica `UPDATE...RETURNING` (estilo sequence).
- Q2 `Filial`: `serie` pode ser por filial (`filial_id` nullable; NULL=global do tenant).
- Q3 `Imposto`: com `vigencia_inicio`/`vigencia_fim` (consulta por data do doc); INV-026.
- Q4 `AuditoriaConfig`: WORM Padrão B; export B2 diferido (GATE), igual outros módulos.
- Q5 RBAC: confirmar com tech-lead que US-CFG-004 é fachada de leitura sobre `authz`, sem schema novo.

## 8. Próximo passo

P1 spec do núcleo (Empresa/Filial + Imposto/RegimeTributario + SerieDocumento) → P2 revisão
`tech-lead` (+ `advogado` no ângulo tributário/retenção) → P3 plan → tasks → fatias.
Investigação por Explore "very thorough" + leitura direta de fiscal/os/calibracao models.
Sem alteração de código.
