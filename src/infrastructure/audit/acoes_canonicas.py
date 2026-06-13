"""Enum canonico de acoes de evento de dominio (BLOQ-A1 advogado).

Lista mantida em sincronia com o conjunto de eventos publicados via
`publicar_evento`. CHECK constraint do banco (`bus_outbox_acao_enum
_semantico`) garante o formato slug `dominio.entidade.op[.var]`; este
modulo garante o conjunto FECHADO de valores permitidos.

Cada modulo Wave A adiciona suas acoes com PR revisado pelo tech-lead
e auditor de seguranca. Manter ordenado por dominio.entidade.

Por que aqui (e nao no dominio): a tabela `bus_outbox` mora em F-A
(infrastructure/audit) — manter o enum aqui evita dependencia reversa
infrastructure -> domain.
"""

from __future__ import annotations

from typing import Final

# Marco 1 `clientes` — US-CLI-001..006.
ACOES_CLIENTES: Final[frozenset[str]] = frozenset(
    {
        "cliente.criado",
        "cliente.atualizado",
        "cliente.mesclado",
        "cliente.bloqueado",
        "cliente.desbloqueado",
        "cliente.importado_csv",
        "cliente.consentimento_revogado",
        "cliente.dados_eliminados",
        "cliente.dados_anonimizados",
        "cliente.dados_exportados",
        # T-CLI-119 (US-CLI-006 AC-006-6) — incidente PII (Res. ANPD 15/2024)
        "cliente.pii.incidente_detectado",
    }
)

# Eventos sistema (modo_sistema=1) — sem tenant_id.
ACOES_SISTEMA: Final[frozenset[str]] = frozenset(
    {
        "sistema.tenant_provisionado",
        "sistema.tenant_offboarded",
        "sistema.outbox_envenenado",
        # T-CLI-104 — circuit breaker observado AcessoDadosCliente
        "sistema.breaker_acesso_pii.disparado",
        "sistema.breaker_acesso_pii.normalizado",
        # T-EQP-027 (AC-EQP-003-4) — lockout 24h disparado por excesso de
        # 4xx no QR publico (>=100 4xx em 1h por IP). Payload sanitizado:
        # ip_hash, janela_temporal, contagem_4xx, lockout_ate.
        "sistema.qr_lockout_disparado",
        # T-EQP-032 (AC-EQP-003-9 / P-EQP-S2) — rate-limit global por
        # tenant excedido em /v1/qr/* (cross-tenant ou anonimo).
        # Payload sanitizado: tenant_id, janela_dia, contagem_requests,
        # limite_calculado, n_equipamentos_ativos.
        "sistema.qr_scraping_suspeito",
        # T-EQP-056 (AC-EQP-006-6 / P-EQP-R9) — provisorio TTL D+7
        # vencido sem promocao. Alerta P2 stub Marco 2; consumer real
        # Wave A PagerDuty. Payload: provisorio_id, tag_provisoria,
        # tenant_id_alvo, expirado_em.
        "sistema.provisorio_expirado",
    }
)

# Marco 2 `responsavel_tecnico` (US-EQP-007 / P-EQP-R10) — gestao do RT do tenant.
ACOES_RT: Final[frozenset[str]] = frozenset(
    {
        "tenant.rt.cadastrado",
        "tenant.rt.encerrado",
        "tenant.rt.trocado",
        "tenant.rt.competencia_declarada",
    }
)

# Marco 2 `equipamentos` (US-EQP-001..006).
ACOES_EQUIPAMENTOS: Final[frozenset[str]] = frozenset(
    {
        "equipamento.criado",
        # T-EQP-009 (AC-EQP-001-7b / P-EQP-T4) - promocao D<C<B<A do
        # perfil_tenant_snapshot via SECURITY DEFINER. 25a WORM (RBC).
        "equipamento.perfil_promovido",
        # T-EQP-017 (AC-EQP-002-6 / INV-EQP-VERSAO-002) - versao criada
        # de campo descritivo. Payload sanitizado (5 campos positivos,
        # 7 proibidos). 25a WORM (RBC + ISO 17025 cl. 8.4).
        "equipamento.versao_criada",
        # T-EQP-022 (US-EQP-002b AC-EQP-002b-5) - 3 transicoes terminais
        # da Aprovacao gestor_qualidade. Cadeia auditavel ISO 17025
        # cl. 6.2 (segregacao de funcoes) + RBC. 25a WORM.
        "equipamento.versao_aprovada",
        "equipamento.versao_rejeitada",
        "equipamento.versao_expirada",
        # T-EQP-040 (US-EQP-004 AC-EQP-004-7) - efetivacao de
        # transferencia de equipamento entre clientes (mesmo tenant).
        # Payload sanitizado: cedente_id_hash + cessionario_id_hash +
        # transferencia_id + motivo_categoria + texto_termo_versao_id.
        "equipamento.transferido",
        # T-EQP-039 (US-EQP-004 AC-EQP-004-6 / P-EQP-R6) - consentimento
        # granular do cedente sobre visualizacao do historico pos-
        # transferencia. Payload sanitizado: equipamento_id +
        # transferencia_id + consentimento_id + nivel + cedente_id_hash +
        # via_concessao + concedido_em. 25a WORM (LGPD art. 8).
        "equipamento.consentimento_historico_concedido",
        # T-EQP-041 (US-EQP-004 AC-EQP-004-8 / P-EQP-R6) - revogacao
        # posterior do consentimento. Payload sanitizado: equipamento_id
        # + consentimento_id + cedente_id_hash + justificativa_hash +
        # via_revogacao + revogado_em. 25a WORM.
        "equipamento.consentimento_historico_revogado",
        # T-EQP-042 (US-EQP-005 AC-EQP-005-1) — sucatamento basico (sem
        # cert vigente). Payload sanitizado: equipamento_id, sucateado_em,
        # justificativa_hash. 25a WORM RBC NIT-DICLA-021.
        "equipamento.sucateado",
        # T-EQP-043 (US-EQP-005 AC-EQP-005-2 / P-EQP-S9) — sucatamento
        # COM certificado vigente. Disparado adicionalmente ao
        # `equipamento.sucateado` quando tem_cert_vigente_no_momento=True.
        # Payload sanitizado: equipamento_id, sucateado_em,
        # justificativa_hash, texto_modal_versao_id,
        # ciencia_validade_tecnica_registrada=True. 25a WORM.
        "equipamento.sucateado_com_cert_vigente",
        # T-EQP-047+059 (US-EQP-006 AC-EQP-006-1+11 / P-EQP-S3) —
        # recebimento fisico no laboratorio. Payload sanitizado:
        # equipamento_id, recebimento_id, condicao_visual_chegada,
        # status_fluxo_lab, tem_foto, foto_sha256 (hex 64), data_recebimento.
        # ISO 17025 cl. 7.4 + RBC NIT-DICLA-021. 25a WORM.
        "equipamento.recebido",
        # T-EQP-050 (US-EQP-006 AC-EQP-006-3b) — transicao na maquina
        # status_fluxo_lab. Payload sanitizado: equipamento_id,
        # recebimento_id, status_origem, status_alvo, tem_observacao.
        # 25a WORM.
        "equipamento.recebimento_transicionado",
        # T-EQP-048 (US-EQP-006 AC-EQP-006-2) — decisao
        # `contatar_cliente_aguardando` dispara consumer
        # NotificacaoClienteService (stub Marco 2). Payload sanitizado.
        # 5a retencao (operacional, nao tecnico).
        "equipamento.notificacao_cliente_aguardando",
        # T-EQP-051 (US-EQP-006 AC-EQP-006-4) — devolucao do equipamento
        # ao cliente. Encerra ciclo do laboratorio (CC art. 624 fim do
        # deposito + ISO 17025 cl. 7.4.5 + CPC art. 411 III). Payload
        # sanitizado: equipamento_id, recebimento_id, devolucao_id,
        # condicao_visual_devolucao, foto_sha256, termo_versao_id,
        # termo_aceite_hash, devolvido_em. 25a WORM.
        "equipamento.devolvido",
        # T-EQP-053 (US-EQP-006 AC-EQP-006-6 / INV-EQP-PROV-001 /
        # Caminho A Roldao) — recebimento provisorio (equipamento sem
        # cadastro completo). Payload sanitizado: provisorio_id,
        # tag_provisoria, condicao_visual_chegada, foto_sha256,
        # ttl_expira_em, data_recebimento. 25a WORM.
        "equipamento.recebido_provisoriamente",
        # T-EQP-053 — promocao do provisorio a equipamento definitivo.
        # Payload sanitizado: provisorio_id, equipamento_id (criado),
        # recebimento_id (1o canonico), tag_canonica, promovido_em.
        # 25a WORM (cadeia de evidencia).
        "equipamento.promovido_de_provisorio",
        # T-EQP-055 (US-EQP-006 AC-EQP-006-7b / P-EQP-R3) — alerta P3
        # stub disparado quando recebimento e gravado sem nenhuma
        # medicao ambiental E sem justificativa textual. Marco 2:
        # consumer real Wave A; alerta correlato P3 telemetria.
        # Payload sanitizado: equipamento_id, recebimento_id,
        # data_recebimento. Sem PII.
        "equipamento.recebimento_sem_ambiente",
        # T-EQP-054 (US-EQP-006 AC-EQP-006-7 / P-EQP-T9) — sweep job
        # detectou equipamento orfao (cliente_atual_id NULL +
        # status nao terminal) e marcou orfao_pendente_decisao.
        # Defesa em profundidade do trigger PG
        # `equipamento_anti_orfao_imediato_trg`. Payload sanitizado:
        # equipamento_id, status_anterior, motivo. Sem PII.
        "equipamento.orfao_marcado_pelo_job",
        # T-EQP-054 (US-EQP-002b AC-EQP-002b-2 / P-EQP-R5) — alerta
        # D-1 antes do SLA vencer disparado pelo job diario. Marco 2:
        # alerta operacional P3 stub; consumer real Wave A enviara
        # email/push ao decisor. Payload sanitizado: aprovacao_id,
        # equipamento_id, sla_vencimento, horas_restantes.
        "equipamento.versao_aprovacao_alerta_d1",
    }
)

# F-C1 P4 (INV-ADMIN-003) — break-glass account lifecycle.
# Eventos sistema-level (tenant_id=None / cadeia sistema), exigem run_as_system.
ACOES_ADMIN_BREAK_GLASS: Final[frozenset[str]] = frozenset(
    {
        # criacao via `manage.py criar_admin_recovery` — grava na cadeia
        # imutavel pra LGPD/CGCRE poder responder "quem criou conta
        # break-glass em data Y?". Payload sanitizado: usuario_id, email
        # (vai pra event_helpers redaction), forcar_rotacao_senha, criado_via.
        "Admin.BreakGlass.CONTA_CRIADA",
        # cada login da conta dispara alerta CRITICO; cravado na cadeia
        # alem da linha em `admin_access`.
        "Admin.BreakGlass.Usado",
    }
)

# Marco 3 `ordens_servico` — US-OS-001..015 (Fase 5).
ACOES_OS: Final[frozenset[str]] = frozenset(
    {
        # OS (agregado raiz)
        "os.aberta",
        "os.atribuida",
        "os.concluida",
        "os.cancelada",
        "os.reaberta",
        "os.escopo_alterado",
        # AtividadeDaOS (filha)
        "os.atividade_adicionada",
        "os.atividade_iniciada",
        "os.atividade_concluida",
        "os.atividade_nao_conforme",
        "os.atividade_nc_resolvida",
        "os.atividade_cancelada",
        "os.atividade_reagendada",
        "os.atividade_tecnico_transferido",
        # Aceite / dispensa / no-show
        "os.no_show_cliente",
        "os.dispensa_aceite_emitida",
        "os.aceite_coletado",
    }
)


# Marco 4 `metrologia/calibracao` — Integration Events (INT-02 Onda PRE-A.4
# auditoria 10 lentes pré-Wave A). Subset dos 23 TIPO_EVENTO_CALIBRACAO_CHOICES
# da migration 0009 que cruzam pro `bus_outbox` (consumer cross-modulo).
# Eventos puramente locais (recepcao, configuracao, leitura_registrada, etc.)
# nao entram aqui — vivem so na trilha WORM `evento_de_calibracao` hash-chain.
ACOES_CALIBRACAO: Final[frozenset[str]] = frozenset(
    {
        # Estados-finais — disparam Marco 5 certificados + qualidade NC + financeiro
        "calibracao.aprovada",
        "calibracao.rejeitada",
        "calibracao.cancelada",
        # Revisao + 2a conferencia (cl. 7.8.6 + ADR-0026)
        "calibracao.revisada_primeira",
        "calibracao.revisao_rejeitada",
        "calibracao.segunda_conferencia_aprovada",
        # NC ISO 17025 cl. 7.10 — qualidade + comunicacao-omnichannel consomem
        "calibracao.nc_aberta",
        "calibracao.nc_resolvida",
        # Reclamacao cl. 7.9
        "calibracao.reclamacao_aberta",
        "calibracao.reclamacao_respondida",
        # Subcontratacao cl. 6.6 (US-CAL-017)
        "calibracao.subcontratada",
        "calibracao.recebida_do_lab",
    }
)


# Marco 5 `metrologia/padroes` — US-PAD-001..009 (GATE-OBS-PAD-WORM-1 / D-PAD-6).
# As 6 mutacoes REST de padrao emitem cadeia WORM `padrao.*` (baixar/revogar
# afetam validade de certificado emitido — cl. 8.4). Consumers Wave A:
# certificados (recall por rastreabilidade revogada), qualidade (NC), bus.
ACOES_PADROES: Final[frozenset[str]] = frozenset(
    {
        "padrao.cadastrado",
        "padrao.recal_externo_iniciado",
        "padrao.recal_externo_retornado",
        "padrao.recal_externo_concluido",  # aprovacao RT — INV-PAD-006 (incertezas mutam)
        "padrao.recal_externo_rejeitado",
        "padrao.baixado",
        "padrao.rastreabilidade_revogada",  # C-5 — dispara recall cl. 8.4 (certificados)
        "padrao.vinculo_auxiliar_criado",  # US-PAD-007-4 cl. 6.4.5 (ativa INV-PAD-007)
        "padrao.vinculo_auxiliar_revogado",
    }
)


# M6 metrologia/escopos-cmc (T-ECMC-031/053) — cadastro/versionamento/revogacao do
# escopo de acreditacao CGCRE + extracao PDF (Fatia 4). Probatorias cl. 8.4 (TL-C-06).
ACOES_ESCOPOS_CMC: Final[frozenset[str]] = frozenset(
    {
        "escopos_cmc.cadastrado",
        "escopos_cmc.revisado",
        "escopos_cmc.revogado",
        "escopos_cmc.extracao_importada",  # T-ECMC-051 — staging RASCUNHO criado
        "escopos_cmc.extracao_confirmada",  # T-ECMC-052 — conferencia humana promoveu
    }
)


# M7 metrologia/procedimentos-calibracao (T-PROC-036) — cadastro/publicacao/
# versionamento/revogacao do procedimento tecnico documentado controlado
# (cl. 7.2.1). Probatorias cl. 8.4 (documento controlado cl. 8.3).
ACOES_PROCEDIMENTOS_CALIBRACAO: Final[frozenset[str]] = frozenset(
    {
        "procedimentos_calibracao.cadastrado",
        "procedimentos_calibracao.publicado",
        "procedimentos_calibracao.revisado",
        "procedimentos_calibracao.revogado",
    }
)


# M8 metrologia/certificados (T-CER-047) — emissao metrologica do certificado.
# PascalCase (nao slug lowercase) PROPOSITAL: vai SO na cadeia hash central
# (cadeia=True, outbox=False), nao no bus_outbox — cujo CHECK exige slug lowercase
# (migration 0011). Precedente: Admin.BreakGlass.CONTA_CRIADA. `CertificadoEmitido`
# (normativo cl. 7.8) e RESERVADO p/ a assinatura A3 (Wave A) — NAO usar aqui:
# status='emitido' interno = emissao metrologica, nao distribuivel ate a A3.
ACOES_CERTIFICADOS: Final[frozenset[str]] = frozenset(
    {
        "Certificados.CertificadoReconciliado",
    }
)


# M9 metrologia/licencas-acreditacoes (T-LIC-044) — cadastro/renovacao/modo
# emergencial/revogacao de documento regulatorio da empresa (acreditacao CGCRE,
# ART/RRT, licencas). Probatorias cl. 8.4 (documento regulatorio controlado). Slug
# lowercase (vao ao bus_outbox — molde escopos_cmc/procedimentos).
ACOES_LICENCAS: Final[frozenset[str]] = frozenset(
    {
        "licencas.documento_cadastrado",
        "licencas.documento_renovado",
        "licencas.modo_emergencial_acionado",
        "licencas.documento_revogado",
    }
)


# Frente fiscal/NFS-e (T-FIS-030/031) — emissao/cancelamento de NFS-e de servico.
# Probatorias fiscais (retencao 5a — INV-FIS-008). Slug lowercase (vao ao
# bus_outbox; `fiscal.nfse_emitida` tem consumer cross-modulo previsto
# contas-receber — D-FIS-9/INV-FIS-CR-001).
ACOES_FISCAL: Final[frozenset[str]] = frozenset(
    {
        "fiscal.nfse_emitida",
        "fiscal.nfse_cancelada",
    }
)


# Frente configuracoes-sistema (T-CFG-033) — mudancas de configuracao do tenant
# (empresa/filial/imposto/serie). PascalCase PROPOSITAL (nomes da spec US-CFG-001
# `Config.EmpresaAtualizada`): vao SO na cadeia hash central (cadeia=True,
# outbox=False) — o CHECK do bus_outbox exige slug lowercase (precedente
# Certificados.CertificadoReconciliado). Reserva de numero NAO gera evento Config
# (consumo operacional de alto volume; trilha fica com o emissor + tabela
# numero_documento_reservado).
ACOES_CONFIG: Final[frozenset[str]] = frozenset(
    {
        "Config.EmpresaAtualizada",
        "Config.FilialAdicionada",
        "Config.FilialEditada",
        "Config.ImpostoCadastrado",
        "Config.ImpostoVigenciaEncerrada",
        "Config.SerieCriada",
    }
)


# Frente produtos-pecas-servicos (T-PPS-034) — catalogo do tenant + TabelaPreco
# (ADR-0081). PascalCase PROPOSITAL (shape do modelo-de-dominio — D-PPS-9): vao
# SO na cadeia hash central (cadeia=True, outbox=False); promocao a outbox e
# GATE-PPS-OUTBOX-ESTOQUE. LGPD (ADV-PPS-01/02): payload leva
# `criado_por_id_hash` + `descricao_hash`/`motivo_hash` (HMAC-tenant ADR-0029);
# `Catalogo.ImportacaoConcluida` leva o SHA-256 do arquivo (prova permanente
# de integridade — staging expira em 90d, o evento WORM nao; ADV-PPS-06).
ACOES_CATALOGO: Final[frozenset[str]] = frozenset(
    {
        "Catalogo.ItemCadastrado",
        "Catalogo.PrecoAlterado",  # nova versao E correcao (payload distingue)
        "Catalogo.ItemInativado",
        "Catalogo.KitAlterado",
        "Catalogo.TabelaCriada",
        "Catalogo.LinhaPrecoCriada",
        "Catalogo.LinhaPrecoCorrigida",
        "Catalogo.LinhaPrecoEncerrada",
        "Catalogo.ImportacaoConcluida",  # T-PPS-042 — lote em staging criado
        # P9 OBS-M1 — rejeicao e decisao humana one-shot; staging expira em 90d,
        # sem evento a decisao sumiria sem rastro permanente.
        "Catalogo.LinhaImportacaoRejeitada",
    }
)


# Frente precificacao (T-PRC-037) — regras de formacao, faixas de desconto,
# aprovacoes de desconto, parametros e perfil de composicao.
# PascalCase PROPOSITAL (shape do modelo-de-dominio — D-PRC-9): vao SO na cadeia
# hash central (cadeia=True, outbox=False — segredo comercial; custo/margem NUNCA
# em claro — INV-PRC-SEGREDO-LOG). Payload NUNCA inclui Parametros/Faixas em claro.
ACOES_PRECIFICACAO: Final[frozenset[str]] = frozenset(
    {
        # US-PRC-001 — publicar / revogar regra de formacao de preco por item
        "Precificacao.RegraPublicada",
        "Precificacao.RegraRevogada",
        # US-PRC-003/004 — aprovacao de desconto one-shot WORM
        "Precificacao.AprovacaoSolicitada",
        "Precificacao.AprovacaoDecidida",
        # US-PRC-004 — configuracoes do tenant (faixas replace-all, perfil, parametros)
        "Precificacao.FaixasDescontoAlteradas",
        "Precificacao.PerfilComposicaoAlterado",
        "Precificacao.ParametrosAlterados",
        # AC-PRC-005-1 — vinculo cliente <-> tabela de preco (MÉDIO-2 P9)
        "Precificacao.VinculoTabelaCriado",
        "Precificacao.VinculoTabelaRevogado",
    }
)


# Frente colaboradores (T-COL-036) — Wave A nível 2.
# Eventos cross-módulo via outbox=True (6 consumers INV-INT-011 — módulos futuros).
# PII pseudonimizada por evento (D-COL-8 / ADV-COL-06): cpf_hash, nome_hash,
# ator_id_hash, motivo_hash via HMAC-tenant (ADR-0029/0064). UUIDs/refs em claro.
ACOES_COLABORADORES: Final[frozenset[str]] = frozenset(
    {
        "colaborador.cadastrado",
        "colaborador.papel_atribuido",
        "colaborador.papel_revogado",
        "colaborador.habilidade_atualizada",
        "colaborador.desligado",
        # AC-COL-04 / D-COL-14 / INV-COL-COMISSAO-AUDIT — alteração de comissão
        # grava trilha auditável via outbox (PATCH partial_update).
        "colaborador.comissao_alterada",
        # Contrato futuro — materialização no GATE-LGPD-RAT-CONSOLIDACAO (A5)
        "colaborador.anonimizado",
    }
)


ACOES_CANONICAS: Final[frozenset[str]] = (
    ACOES_CLIENTES
    | ACOES_SISTEMA
    | ACOES_RT
    | ACOES_EQUIPAMENTOS
    | ACOES_ADMIN_BREAK_GLASS
    | ACOES_OS
    | ACOES_CALIBRACAO
    | ACOES_PADROES
    | ACOES_ESCOPOS_CMC
    | ACOES_PROCEDIMENTOS_CALIBRACAO
    | ACOES_CERTIFICADOS
    | ACOES_LICENCAS
    | ACOES_FISCAL
    | ACOES_CONFIG
    | ACOES_CATALOGO
    | ACOES_PRECIFICACAO
    | ACOES_COLABORADORES
)


def assert_acao_canonica(acao: str) -> None:
    """Helper pra chamador validar antes de `publicar_evento`.

    O banco tambem valida via CHECK; aqui eh fail-fast em camada Python
    (mensagem clara) — defesa em profundidade.
    """
    if acao not in ACOES_CANONICAS:
        raise ValueError(
            f"acao '{acao}' nao esta em acoes_canonicas.ACOES_CANONICAS. "
            "Cada acao nova exige PR + revisao do tech-lead + auditor de "
            "seguranca (BLOQ-A1 advogado)."
        )
