"""Tabelas de autorização (ADR-0012 + INV-AUTHZ-001..003).

3 tabelas:

1. `Perfil` — catálogo de perfis (admin_tenant, tecnico, rt_signatario, ...).
   tenant_id NULL = perfil global do sistema (catálogo Aferê); UUID = perfil
   específico de um tenant (Wave A+).

2. `PerfilAcao` — matriz papel × ação. Cada linha diz se um perfil pode
   executar uma ação. Ações no formato "modulo.acao" (ex: "os.criar",
   "certificado.emitir").

3. `AuthzDecision` — audit trail SÍNCRONO de toda decisão `can()`. Imutável
   (trigger PG anti-UPDATE/DELETE — migration 0003) + hash chain entre
   linhas. INV-AUTHZ-002 cravada aqui.

UsuarioPerfilTenant (em src/infrastructure/usuario/models.py) já mapeia
usuário × tenant × perfil — F-A criou. Esta app só adiciona o catálogo
e a matriz. Em Wave A vamos refatorar `perfil: CharField` pra FK quando
o catálogo crescer.
"""

from __future__ import annotations

import uuid

from django.db import models


class Perfil(models.Model):
    """Catálogo de perfis. Codigo bate com `UsuarioPerfilTenant.perfil`.

    Perfis seed (criados na migration 0004):
    - `admin_tenant`: dono/gestor do tenant; pode ler/escrever tudo do
      próprio tenant. NÃO vê dados pessoais de demitidos (LGPD).
    - `tecnico`: técnico de campo; lê OS atribuída a ele, escreve diário
      de execução. Não vê financeiro nem dados de cliente além do necessário.
    - `rt_signatario`: Responsável Técnico acreditado RBC; assina
      certificado dentro do escopo vigente (ABAC entra em Wave A).
    - `cliente_externo_leitura`: cliente final; vê só seus próprios
      registros (portal cliente — Wave B).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=50,
        unique=True,
        help_text="Slug do perfil (ex: 'admin_tenant'). Bate com UsuarioPerfilTenant.perfil.",
    )
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tenant_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="NULL = perfil global do sistema. UUID = perfil específico de tenant (Wave A+).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "authz"
        db_table = "authz_perfil"
        verbose_name = "Perfil de autorização"
        verbose_name_plural = "Perfis de autorização"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return self.codigo


class PerfilAcao(models.Model):
    """Matriz `perfil × ação`. Linha existe = permissão concedida.

    Ações no formato "modulo.acao" (ex: "os.criar", "certificado.emitir",
    "fatura.estornar"). Crescente — catálogo formaliza em Wave A
    (`docs/comum/acoes-catalogo.md` a criar).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(
        Perfil,
        on_delete=models.PROTECT,
        related_name="acoes_permitidas",
    )
    acao = models.CharField(
        max_length=100,
        help_text="Slug 'modulo.acao' (ex: 'os.criar').",
    )
    pode_executar = models.BooleanField(
        default=True,
        help_text=(
            "False = bloqueio explícito que sobrepõe herança (raro). True = "
            "permite. Ausência da linha = sem permissão (deny-by-default)."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "authz"
        db_table = "authz_perfil_acao"
        verbose_name = "Permissão por perfil"
        verbose_name_plural = "Permissões por perfil"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "acao"],
                name="uq_authz_perfil_acao",
            ),
        ]
        indexes = [
            models.Index(fields=["acao"], name="ix_authz_acao"),
        ]

    def __str__(self) -> str:
        return f"{self.perfil.codigo}:{self.acao}={'✓' if self.pode_executar else '✗'}"


class AuthzDecision(models.Model):
    """Audit trail síncrono de cada chamada `can()` (INV-AUTHZ-002).

    Tabela imutável: trigger PG bloqueia UPDATE/DELETE (migration 0003).
    Hash chain entre linhas garante detecção de truncate.

    `tenant_id` é NULL pra decisões pré-tenant (login, lista de tenants
    do usuário, etc) — caso contrário sempre preenchido.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="NULL pra decisões pré-tenant (login, listar tenants).",
    )
    action = models.CharField(max_length=100, db_index=True)
    resource_summary = models.JSONField(
        default=dict,
        help_text="Snapshot mínimo do recurso (sem PII cru).",
    )
    purpose = models.CharField(
        max_length=50,
        help_text="Finalidade LGPD: 'execucao_contrato', 'cumprimento_obrigacao_legal', etc.",
    )
    decision = models.CharField(
        max_length=20,
        choices=[("allowed", "allowed"), ("denied", "denied")],
    )
    reason = models.CharField(
        max_length=200,
        help_text="String curta estável (ex: 'rbac_denied', 'feature_disabled').",
    )
    perfis_aplicados = models.JSONField(
        default=list,
        help_text="Lista de codigos de perfil que pesaram (['tecnico']).",
    )
    escopo_avaliado = models.JSONField(
        default=dict,
        help_text="JSON com atributos ABAC consultados.",
    )
    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 do IP do request (sem armazenar IP cru — LGPD).",
    )
    hash_anterior = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="SHA-256 da linha anterior na cadeia. NULL = primeira linha.",
    )
    hash_atual = models.CharField(
        max_length=64,
        help_text="SHA-256(hash_anterior || payload_canonico_desta_linha).",
    )
    # FB-C1: ordem monotonica da cadeia (SEQUENCE — espelha audit/0009).
    # Encadeamento e por-tenant OU por-usuario (cadeia pre-tenant); sequencia
    # so desempata (timestamp colide em µs sob o advisory lock). `db_default`
    # faz o INSERT do ORM emitir DEFAULT — a sequence (authz/0004) preenche.
    sequencia = models.BigIntegerField(
        editable=False,
        db_default=models.Func(
            models.Value("authz_decisions_seq"), function="nextval"
        ),
    )

    class Meta:
        app_label = "authz"
        db_table = "authz_decisions"
        verbose_name = "Decisão de autorização (audit)"
        verbose_name_plural = "Decisões de autorização (audit)"
        ordering = ["sequencia"]
        indexes = [
            models.Index(
                fields=["tenant_id", "sequencia"],
                name="ix_authzdec_tenant_seq",
            ),
            # FB-C1 (review tech-lead Q2): índice PARCIAL exatamente o caminho
            # de leitura da cadeia pré-tenant POR-USUÁRIO — `.first()` O(log n)
            # dentro do advisory lock (sem ele = seq scan segurando o lock).
            models.Index(
                fields=["usuario_id", "sequencia"],
                name="ix_authzdec_user_seq_pretenant",
                condition=models.Q(tenant_id__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        ts = self.timestamp.isoformat() if self.timestamp else "?"
        return f"{ts} {self.decision} {self.action}"
