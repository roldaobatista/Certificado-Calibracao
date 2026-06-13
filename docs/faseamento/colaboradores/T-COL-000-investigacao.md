---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: colaboradores
tipo: investigacao-p0
relacionados:
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/modelo-de-dominio.md
  - docs/adr/0016-operacao-consistente.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# T-COL-000 — Investigação regra #0 — frente `colaboradores` (#4 da cadeia)

> **Pra quê:** ler o estado REAL (código + docs + decisões) antes de escrever spec.
> Molde: `docs/faseamento/precificacao/T-PRC-000-investigacao.md`.
> Ordem cravada (`plano-dependencia-sistema.md` §7): #1 configuracoes-sistema ✅ →
> #2 produtos-pecas-servicos ✅ → #3 precificacao ✅ (FECHADA 2026-06-13) →
> **#4 colaboradores (base, seed habilidade estático)** → #5 orcamentos.
>
> Fonte: 3 subagentes Explore (código/seams · consumidores+eventos · INVs/ADRs/LGPD+Família 0),
> 2026-06-13. Tudo verificado em `src/` real — não na memória.

## 1. Estado real do código — GREENFIELD TOTAL

- **Zero código:** grep `colaborador|Colaborador|Habilidade|CatalogoHabilidade|comissao_default`
  em `src/` → **0 ocorrências**. Não existe `src/{domain,application,infrastructure}/colaboradores/`.
- **Família 0 COMPLETA (status draft):** PRD + modelo-de-domínio + glossário (15 termos) +
  personas (5+anti) + métricas (M-COL-01..08, north star ≥95% alocação bate matriz) +
  contratos `api.md`/`ui.md`/`exports.md`. A spec recorta sobre eles, não inventa.
- **Catálogo de eventos já prevê o módulo:** `Colaborador.Cadastrado/PapelAtribuido/
  PapelRevogado/HabilidadeAtualizada/Desligado` em `integracoes-inter-modulos.md:537-546`.

## 2. Seams prontos (consumir, não recriar)

| Peça | Onde | Uso pela frente |
|------|------|-----------------|
| VO `CPF` (11 díg + DV mód-11) e `CNPJ` (alfanum ADR-0017) normalizados | `src/domain/shared/value_objects.py:73,137` | validação CPF do colaborador (não reimplementar) |
| Molde dedup INV-024: UNIQUE **parcial** `WHERE deletado_em IS NULL` + `clean()` instancia VO | `clientes/migrations/0006_unique_doc_ativo.py:16` + `clientes/models.py:293` | dedup CPF por tenant (INV-COL-CPF a criar) |
| Soft-delete Padrão C (`deletado_em`/`_por_usuario_id`/`_motivo`) + manager filtra + `all_objects` | `clientes/models.py:34,236,252` | desligamento do colaborador (ativo derivado) |
| Histórico imutável: FK PROTECT `db_constraint=False` p/ inativo referenciável (INV-025) | `clientes/models.py:496,526` | colaborador desligado referenciado em OS/cert |
| `responsavel_tecnico` (`ResponsavelTecnicoTenant` + `RTCompetencia` EXCLUDE GIST) + predicate `decisor_tem_competencia_para_atividade` | `infrastructure/responsavel_tecnico/{models,predicates,services_rt}.py` | FK do papel SIGNATARIO (INV-003) — escopo vigente na data |
| WORM Padrão B molde `Imposto`/`RegraFormacaoPreco` + triggers PG (probatório imutável, block delete, one-shot) | `configuracoes_sistema/models.py:145` + `precificacao/migrations/0003_triggers_worm.py` | versionar o que precisar ser WORM (avaliar p/ Papel/Habilidade — ver §5) |
| VO `JanelaVigencia` (ADR-0030, INV-VIG-001..004) | `src/domain/shared/value_objects.py:185` | vigência de papel/habilidade/competência |
| Seed estático via `RunPython` (DISABLE RLS no contexto migração + idempotente) | `precificacao/migrations/0008_seed_faixas_default.py:42,138` + `authz/migrations/0003_seed_perfis.py` | seed `CatalogoHabilidade` estático |
| REST molde: `_PrecificacaoViewSetBase` (ViewSet), idempotência 2 camadas (`_aplicar_idempotencia`/`concluir_chave`/`falhar_chave`), `ACTION_MAP` authz, `publicar_evento`, perfil server-side `_pode_ver_*` fail-closed, `authz_purpose` LGPD | `precificacao/_views_suporte.py:50,85,115,226` + `views.py` | REST da frente nasce no molde (mascaramento por papel) |
| Anexo: porta `AnexoStoragePort` (Protocol, SHA-256 server-side) + `AnexoStorageLocal` content-addressed | `application/metrologia/procedimentos_calibracao/anexo_storage.py:17` + `.../anexo_storage_local.py:30` | CTPS/CNH/ASO/foto — B2 WORM real diferido (GATE) |
| Foto com EXIF strip + MIME/5MB + SHA-256 (Padrão BYTEA Marco 2) | `equipamentos/services_foto_storage.py` | foto do colaborador (+ blur se rosto identificável — LGPD §4) |
| Path: infra **sempre flat** `src/infrastructure/<modulo>/`; domain flat (precificacao/pps) ou aninhado por domínio (`comercial/clientes`) | precificacao/pps/clientes | decisão de path domain → tech-lead P2 |

## 3. Contrato do evento `Colaborador.Desligado` (6 consumers — todos FUTUROS)

- **Payload v9** (`integracoes-inter-modulos.md:826`): envelope canônico + `payload:
  {colaborador_id, is_rt_signatario: bool, tipos_servico_assinava: list[str],
  comissoes_pendentes_count: int}`. Alias legado `ColaboradorDesligado` (remoção 2026-12-31).
- **INV-INT-011** (`REGRAS-INEGOCIAVEIS.md:557`, ADR-0016:58-68): **6 consumers em ≤2s** —
  (a) acesso-seguranca encerra sessões web+mobile JWT + bloqueia login → `AcessoSeguranca.SessoesEncerradasForcado`;
  (b) operacao/os marca OSs `tecnico_desligado_pendente_reatribuicao=true` → `OS.PendenteReatribuicao`;
  (c) financeiro/comissoes `bloqueado_por_desligamento=true` → `Comissoes.ComissaoBloqueadaPorDesligamento`;
  (d) financeiro/caixa-tecnico despesas/adiantamentos "a reconciliar" (sem evento downstream);
  (e) metrologia/certificados se `is_rt_signatario` → INV-INT-002 (`REGRAS:548`) → `Certificados.SignatarioTransicaoIniciada`;
  (f) suporte-saas encerra sessão remota.
- **NENHUM consumer existe em `src/`** (os 6 módulos são futuros). Tratamento: a frente
  **publica** o evento com payload completo; consumo é problema dos módulos a jusante
  (porta fail-open lazy à la ADR-0066). A frente NÃO implementa os 6 reatores.
- **Carga do payload:** `is_rt_signatario`/`tipos_servico_assinava` saem do próprio
  módulo (papel SIGNATARIO + FK RT); `comissoes_pendentes_count` é stub/0 em Wave A
  (comissoes não existe) — candidato a GATE-COL-COMISSAO-COUNT.

## 4. O que os módulos a jusante esperam (referência opaca, não FK estrutural)

- **agenda** consome eventos (`Colaborador.Desligado`, `AusenciaRegistrada`) p/ liberar slots;
  elegibilidade técnica vem de `treinamentos.Habilitacao` via predicate ABAC, **não** lê
  colaboradores direto (`agenda/modelo-de-dominio.md:115`). AC-COL-05 (elegíveis) é endpoint
  `GET /colaboradores/elegiveis` que a Operação chama.
- **os** referencia `tecnico_atribuido_id` / `AtividadeDaOS.tecnico_executor_id` (UUID opaco).
- **comissoes** usa `beneficiario_id` + `comissao_default_pct` (campo direto do Colaborador);
  endpoint `GET /colaboradores/{id}/comissao-vigente`.
- **caixa-tecnico / app-tecnico** usam `tecnico_id` opaco.
- **treinamentos / SST** são donos da trilha (cl. 6.2) e do ASO — `colaborador_id` é a chave;
  colaboradores NÃO modela treinamento/ASO (non-goal). SST publica `TecnicoBloqueadoSemNR`.
- **frota** exige papel `MOTORISTA_UMC` + CNH; jornada Lei 13.103 (INV-020) é de frota/agenda,
  **não** de colaboradores (só vincula papel + CNH).

## 5. RBAC, vínculo login e perfil regulatório

- **RBAC (ADR-0012):** colaboradores **NÃO cria perfis authz**. Publica `PapelAtribuido/Revogado`
  → consumer acesso-seguranca cria/encerra `UsuarioPerfilTenant`. Fronteira: **papel de negócio**
  (TECNICO/SIGNATARIO/ATENDENTE/GERENTE/DONO/QUALIDADE/MOTORISTA_UMC) ≠ **perfil authz**.
  `DjangoAuthorizationProvider` já existe (`infrastructure/authz/django_provider.py`).
- **Vínculo Colaborador↔Usuario(login):** HOJE entidades separadas, **sem FK direta**
  (`usuario/models.py:56` + `UsuarioPerfilTenant:110`). Correlação por UUID. **Decisão de
  modelagem aberta (TÉCNICA → tech-lead P2):** como ligar Colaborador↔Usuario? Nem todo
  colaborador tem login (faxineiro ≠ técnico-de-campo). Recomendação a validar: FK opcional
  `usuario_id?` no Colaborador, provisionamento de login opt-in ao atribuir papel que exige acesso.
- **Perfil regulatório (ADR-0067):** papel SIGNATARIO só tem semântica ISO 17025 em perfil A/B/C;
  em D ("Relatório de Aferição") não há assinatura acreditada → gate `tenant_perfil_e(['A','B','C'])`.
  Retenção do registro do signatário herda prazo do certificado (25a em A/B/C; 5a em D).
  `matriz-feature-perfil.md` **não tem linha** p/ colaborador/papel SIGNATARIO → A8.

## 6. LGPD — colaborador é titular (funcionário), PII pesado

| Dado | Base legal | Retenção | Status no projeto |
|------|-----------|----------|-------------------|
| nome, CPF, e-mail, telefone | art. 7º V (exec. contrato) | vínculo + 5a (crypto-shredding) | RAT-02 cobre genérico |
| CTPS, CNH | art. 7º II (obrigação legal CLT/DETRAN) | **sem linha própria** | **A3/A4 — a declarar** |
| foto | art. 7º V; se rosto → art. 11 §4 (biométrico sensível) | sem linha | **A4 — blur obrigatório se rosto** |
| ASO | art. 11 II "a" (NR-7) | vínculo + 20a (NR-7 vence LGPD) | RAT-14 + DPIA-03 (não-goal MVP) |
| certificados treinamento | art. 7º II (cl. 6.2 + NR) | sem linha | **A3 — a declarar** (mas treinamento é non-goal) |

- **Distinção CLT × PJ importa:** CLT = obrigação legal do empregador; PJ = execução de contrato.
  `vinculo` enum {CLT, PJ, ESTAGIARIO, SOCIO, TERCEIRIZADO} — spec deve reconhecer os dois regimes.
- **Cenário D (esquecimento × retenção):** resolvido por zonas (`retencao-matriz.md:138-147`):
  obrigação legal vence art. 18 VI; **signatário NUNCA é eliminado enquanto cert dentro de 25a**
  (ADR-0021). DRILL-RET-08/09 cobrem ASO.
- **ADR-0032 (FK cross-módulo):** comissão = Zona B (anonimização in-place, 5a Receita);
  ref em OS = Zona A; signatário cert = preservado 25a. `retrofit-fk-pii-anonimizavel.md` FK#7
  já cobre comissão.vendedor_id. Evento `Colaborador.Anonimizado` análogo a `Cliente.Anonimizado` → A5.

## 7. AUSÊNCIAS mapeadas (A1–A10) — classificadas por destino

> **Regra de cerimônia (2026-06-12):** RAT/DPIA/minutas **congelados até GATE-LGPD-RAT-CONSOLIDACAO**.
> As ausências LGPD abaixo **NÃO se escrevem agora** — viram GATE rastreado no P8, não doc novo.

| # | Ausência | Destino | Quando |
|---|----------|---------|--------|
| A1 | `INV-COL-CPF-001` (dedup CPF próprio, não espelho) | invariante nova (REGRAS) + hook | P4/P7 |
| A2 | `INV-COL-INATIVO-001` (hard-delete bloqueado se referenciado) | invariante nova + trigger/hook | P4/P5/P7 |
| A3 | RAT p/ CTPS/CNH/foto/certificados | **GATE-LGPD-RAT-CONSOLIDACAO** (congelado) | rastrear P8 |
| A4 | Retenção CTPS/CNH/foto | **GATE-LGPD-RAT-CONSOLIDACAO** (congelado) | rastrear P8 |
| A5 | Evento `Colaborador.Anonimizado` no catálogo | catálogo eventos | P7 |
| A6 | Zona ADR-0021 por campo do Colaborador | **GATE-LGPD-RAT-CONSOLIDACAO** (congelado) | rastrear P8 |
| A7 | DPIA cadastro colaborador (não-ASO) | **GATE-LGPD-RAT-CONSOLIDACAO** (congelado) | rastrear P8 |
| A8 | Linha matriz-feature-perfil (SIGNATARIO por perfil) | matriz-feature-perfil + hook | P8 |
| A9 | Emenda faseamento-modulos.md (Wave B→A nível 2) | faseamento-modulos.md | P8 |
| A10 | Seed `CatalogoHabilidade` estático em configuracoes-sistema | migration seed | P5 |

## 8. Recorte núcleo Wave A proposto (startável HOJE, zero dependência inexistente)

**NÚCLEO:**
1. `Colaborador` (agregado raiz, PII): nome, `CPF` (VO), e-mail, telefone, foto?, vinculo (enum),
   data_admissao, data_desligamento?, motivo_desligamento?, comissao_default_pct, observacao,
   `usuario_id?` (FK opcional — decisão P2), `ativo` derivado. Soft-delete Padrão C.
2. `Papel` (filha, enum 7): SIGNATARIO exige FK `responsavel_tecnico` (INV-003) + gate perfil A/B/C;
   DONO único por tenant (partial unique WHERE data_fim IS NULL); MOTORISTA_UMC exige CNH (pendência
   marcada, não bloqueio hard — já decidido no modelo). Revogação = `revogado_em` (não deleta).
3. `Habilidade` (filha/matriz): FK `CatalogoHabilidade` OU descrição livre, nivel (APRENDIZ/CAPACITADO/
   MESTRE), evidencia_url?, data_avaliacao.
4. `CatalogoHabilidade` (seed estático global read-only — em configuracoes-sistema, A10).
5. `Documento` (anexo CTPS/CNH/CERTIFICADO/ASO/OUTRO) via `AnexoStoragePort` local; validade só
   armazena (alerta = V2).
6. Desligamento: ativo=false → cascade revoga papéis → publica `Colaborador.Desligado` (payload v9,
   `comissoes_pendentes_count`=0 stub); hard-delete bloqueado se referenciado (INV-COL-INATIVO).
7. Eventos: `Cadastrado`, `PapelAtribuido/Revogado`, `HabilidadeAtualizada`, `Desligado`,
   `Anonimizado` (A5).
8. REST: CRUD + `/papeis` + `/habilidades` + `/documentos` + `GET /elegiveis` + `GET /{id}/comissao-vigente`;
   mascaramento LGPD por papel server-side (CPF só Dono; CTPS/CNH Dono+próprio; etc. — `exports.md`).
   Idempotência + ACTION_MAP authz + audit INV-001 em comissao_default_pct.

**DIFERIDO (GATE-COL-*):** folha/eSocial/ponto/avaliação/benefícios/férias (non-goals PRD);
gestão de validade de treinamento/ASO (módulos treinamentos/SST); B2 WORM real de anexos
(GATE-COL-ANEXO-B2); `comissoes_pendentes_count` real (GATE-COL-COMISSAO-COUNT, quando comissoes existir);
6 consumers do `Colaborador.Desligado` (módulos a jusante); UI (frente de telas); RAT/DPIA/retenção
(GATE-LGPD-RAT-CONSOLIDACAO).

## 9. Decisões abertas (classificadas por dono)

**PRODUTO — Roldão (rodada batch única no P2, com recomendação) — candidatas:**
- D-prod-1: `CatalogoHabilidade` — seed estático mínimo (grandezas metrológicas) **+ habilidade
  livre** (já no modelo) vs catálogo editável pelo tenant. *Recomendação: seed estático + livre
  (modelo já decide); confirmar se o tenant pode adicionar entradas ao catálogo.*
- D-prod-2: mascaramento de CPF — `exports.md` crava "CPF só Dono". Confirmar se Gerente também vê
  (impacta operação do dia a dia). *Recomendação: seguir contrato (só Dono), Gerente vê mascarado.*
- (demais já cravadas na Família 0 — não reabrir: MOTORISTA sem CNH = pendência; soft-delete;
  papel sem escopo = 422; self-service read-only do técnico.)

**TÉCNICA/ARQUITETURA — subagentes (P2):**
- tech-lead: path domain (flat vs aninhado `rh_frota_qualidade/`); vínculo Colaborador↔Usuario
  (FK opcional + provisionamento opt-in); contrato exato `AnexoStoragePort` p/ documentos;
  Papel/Habilidade são WORM (Padrão B) ou mutáveis com audit (Padrão C)? — provável C + revogado_em;
  onde mora `CatalogoHabilidade` (configuracoes-sistema vs módulo próprio).
- advogado: bases legais CLT×PJ por campo; foto biométrica (blur); confirmar que NÃO se escreve
  RAT/DPIA agora (congelado) e só se rastreia GATE; zona ADR-0021 por campo (diferida ao GATE).

## 10. Próximos passos do ritual

P1 spec (recorte §8 sobre PRD draft) → P2 revisões `tech-lead` + `advogado` + rodada batch Roldão
(D-prod-1/2 com recomendação) → P3 plan/tasks (fatias 1a domínio / 1b schema+seed / 2 use cases+REST /
3 P7) → P4..P7 implementação → P8 emendas (A8/A9 + GATEs A3/A4/A6/A7 rastreados) → P9 auditores
roteados (lgpd OBRIGATÓRIO — PII pesado) com 2ª passada escopada + adversarial (INV-RITUAL-001).
