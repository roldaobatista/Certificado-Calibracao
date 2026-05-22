"""DRF views Marco 2 — Equipamento (T-EQP-002 etiqueta PDF + T-EQP-003 Idempotency).

# authz-check: skip -- RequireAuthz global (DEFAULT_PERMISSION_CLASSES)
# resolve via ACTION_MAP — mesmo pattern de clientes/views.py.

Esta task entrega APENAS o endpoint POST `/equipamentos/{id}/etiqueta.pdf`.
CRUD pleno (POST /equipamentos/, PATCH versionado, transferir etc.) fica
para T-EQP-001-CRUD/T-EQP-003+. Por isso o ViewSet aqui e minimo:
list/retrieve + action customizada `etiqueta`.

Autorizacao via RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP:
- `equipamentos.ler` para list/retrieve
- `equipamentos.imprimir_etiqueta` para POST etiqueta.pdf (perfil diferente
  de "ler" — gera artefato fisico)

Multi-tenant (defesa em profundidade ADR-0002):
- queryset filtrado por `active_tenant_context` no ORM
- RLS no banco (POLICY equipamentos_tenant_isolation_*) bloqueia se ORM
  filter for esquecido — falha duro (RLS=FORCE)

Cache 60s (AC-EQP-001-2): `Cache-Control: private, max-age=60` no response.
Cache PRIVATE porque etiqueta tem nome_fantasia do tenant e e por-equipamento.

T-EQP-003 / AC-EQP-001-2b (P-EQP-T6): POST `/etiqueta.pdf` exige header
`Idempotency-Key` UUID. Politica:
- ausente/invalido        -> 400
- mesma chave, em_processo -> 425 (Retry-After: 1)
- mesma chave, payload diferente -> 422
- mesma chave, expirada (>24h) -> 409
- mesma chave, concluida + janela valida -> replay (re-renderiza PDF
  via `garantir_qrcode_vigente` idempotente — mesmo QRCode original)
"""

from __future__ import annotations

from uuid import UUID

from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.multitenant.context import active_tenant_context

from .models import Equipamento
from .serializers import EquipamentoCriarSerializer, EquipamentoLeituraSerializer
from .services_equipamento import (
    DadosCriacaoEquipamento,
    TagDuplicada,
    criar_equipamento,
)
from .services_etiqueta import gerar_etiqueta_pdf

ENDPOINT_ETIQUETA = "equipamentos.etiqueta"
ENDPOINT_CRIAR = "equipamentos.criar"
ENDPOINT_TRANSFERIR = "equipamentos.transferir"
ENDPOINT_REVOGAR_CONSENT_HISTORICO = "equipamentos.revogar_consentimento_historico"
ENDPOINT_SUCATEAR = "equipamentos.sucatear"
ENDPOINT_RECEBER = "equipamentos.receber"
ENDPOINT_TRANSICIONAR_RECEBIMENTO = "equipamentos.transicionar_recebimento"


def _hashear_ip_request(request, tenant_id: UUID) -> str:
    """HMAC do IP da request com salt do tenant — mesmo padrao
    `clientes/views._hashear_ip`."""
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

    ip = (
        request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        or request.META.get("REMOTE_ADDR", "")
    )
    if not ip:
        return ""
    return hashear_pii_com_salt_tenant(ip, tenant_id)


def _active_tenant_obrigatorio() -> UUID:
    """Falsafe pro middleware — `PermissionDenied` se nao houver tenant ativo."""
    active = active_tenant_context.get()
    if active is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active


def _resposta_pdf_etiqueta(equipamento: Equipamento, pdf_bytes: bytes) -> HttpResponse:
    """Monta HttpResponse com cabecalhos canonicos da etiqueta (AC-EQP-001-2)."""
    response = HttpResponse(
        pdf_bytes, content_type="application/pdf", status=status.HTTP_200_OK
    )
    response["Content-Disposition"] = f'inline; filename="etiqueta-{equipamento.tag}.pdf"'
    # AC-EQP-001-2: cache 60s, PRIVATE (tem nome_fantasia do tenant).
    response["Cache-Control"] = "private, max-age=60"
    return response


class EquipamentoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """list/retrieve/create + action `etiqueta` — restante CRUD em T-EQP futuras.

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP.
    """

    serializer_class = EquipamentoLeituraSerializer
    queryset = Equipamento.objects.none()
    authz_purpose = "execucao_contrato"
    lookup_field = "id"
    lookup_value_regex = r"[0-9a-f-]{36}"

    ACTION_MAP = {
        "list": "equipamentos.ler",
        "retrieve": "equipamentos.ler",
        "create": "equipamentos.criar",
        "etiqueta": "equipamentos.imprimir_etiqueta",
        # T-EQP-024 / US-EQP-003 AC-EQP-003-1: ficha 360°.
        "ficha360": "equipamentos.ficha360",
        # T-EQP-034 / US-EQP-004 AC-EQP-004-1: transferir.
        "transferir": "equipamentos.transferir",
        # T-EQP-041 / US-EQP-004 AC-EQP-004-8: revogar consentimento historico.
        "revogar_consentimento_historico": (
            "equipamentos.revogar_consentimento_historico"
        ),
        # T-EQP-042 / US-EQP-005 AC-EQP-005-1: sucatear.
        "sucatear": "equipamentos.sucatear",
        # T-EQP-047 / US-EQP-006 AC-EQP-006-1: receber.
        "receber": "equipamentos.receber",
        # T-EQP-050 / US-EQP-006 AC-EQP-006-3b: transicionar recebimento.
        "transicionar_recebimento": (
            "equipamentos.transicionar_recebimento"
        ),
    }

    def get_authz_action(self, request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request):
        return {}

    def get_queryset(self):
        active = _active_tenant_obrigatorio()
        return Equipamento.objects.filter(tenant_id=active)

    # authz-check: skip -- RequireAuthz global + ACTION_MAP['create'] = 'equipamentos.criar'
    def create(self, request: Request, *args, **kwargs) -> Response:
        """POST /api/v1/equipamentos/ — cadastra equipamento (T-EQP-005+007).

        Exige header `Idempotency-Key` UUID (P-EQP-T6 horizontal F-A).
        TAG duplicada no tenant -> 409 com link pro existente.
        localizacao_fisica com PII -> 400 INV-EQP-LOC-001.
        Publica `equipamento.criado` no bus_outbox (AC-EQP-001-6).
        """
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        ser = EquipamentoCriarSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        chave_header = request.META.get("HTTP_IDEMPOTENCY_KEY")
        avaliacao = avaliar_chave_idempotencia(
            tenant_id=tenant_id,
            usuario_id=user_id,
            endpoint=ENDPOINT_CRIAR,
            chave_header=chave_header,
            payload={
                "tag": ser.validated_data["tag"],
                "numero_serie": ser.validated_data["numero_serie"],
            },
        )
        if isinstance(avaliacao, ErroValidacao):
            return _resposta_erro_idempotencia(avaliacao)
        if isinstance(avaliacao, Replay):
            resumo = avaliacao.response_body_resumo or {}
            eq_id_str = resumo.get("equipamento_id") or ""
            existente = (
                Equipamento.objects.filter(id=eq_id_str, tenant_id=tenant_id).first()
                if eq_id_str
                else None
            )
            if existente is not None:
                return Response(
                    EquipamentoLeituraSerializer(existente).data,
                    status=status.HTTP_200_OK,
                )
            return Response(resumo, status=status.HTTP_200_OK)

        assert isinstance(avaliacao, NovoProcessamento)
        dados = DadosCriacaoEquipamento(
            tag=ser.validated_data["tag"],
            numero_serie=ser.validated_data["numero_serie"],
            fabricante=ser.validated_data["fabricante"],
            modelo=ser.validated_data["modelo"],
            localizacao_fisica=ser.validated_data.get("localizacao_fisica", ""),
            cliente_atual_id=ser.validated_data.get("cliente_atual_id"),
            perfil_tenant_snapshot=ser.validated_data.get("perfil_tenant_snapshot"),
            snapshot_schema_version=ser.validated_data.get(
                "snapshot_schema_version", "1.0.0"
            ),
        )
        try:
            equipamento = criar_equipamento(
                tenant_id=tenant_id,
                criado_por_id=user_id,
                dados=dados,
            )
        except TagDuplicada as exc:
            falhar_chave(
                chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=409,
            )
            return Response(
                {
                    "codigo": "tag_duplicada",
                    "detalhe": str(exc),
                    "equipamento_existente_id": str(exc.equipamento_id_existente),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception:
            falhar_chave(
                chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=500,
            )
            raise
        concluir_chave(
            chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            response_status=201,
            response_body_resumo={"equipamento_id": str(equipamento.id)},
        )
        return Response(
            EquipamentoLeituraSerializer(equipamento).data,
            status=status.HTTP_201_CREATED,
        )

    # authz-check: skip -- RequireAuthz global + ACTION_MAP['etiqueta'] = 'equipamentos.imprimir_etiqueta'
    @action(detail=True, methods=["post"], url_path="etiqueta.pdf")
    def etiqueta(self, request: Request, id: str | None = None) -> Response | HttpResponse:
        """POST `/equipamentos/{id}/etiqueta.pdf` — gera/retorna PDF.

        Exige header `Idempotency-Key` (UUID). 2a chamada com mesma chave
        retorna o MESMO PDF (mesmo QRCode original), re-renderizado.

        Idempotente: chamadas repetidas reusam o QRCode vigente (UNIQUE
        no hash); cada chamada renderiza PDF fresco (cache HTTP 60s
        encurta esse custo em UI).
        """
        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        # IsAuthenticated em DEFAULT_PERMISSION_CLASSES garante user autenticado
        # antes do handler; user.id e UUID nao-nulo. Assert defensivo.
        user_id = request.user.id
        assert user_id is not None
        usuario_id: UUID = user_id

        chave_header = request.META.get("HTTP_IDEMPOTENCY_KEY")
        avaliacao = avaliar_chave_idempotencia(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_ETIQUETA,
            chave_header=chave_header,
            payload={"equipamento_id": str(equipamento.id)},
        )
        if isinstance(avaliacao, ErroValidacao):
            return _resposta_erro_idempotencia(avaliacao)

        if isinstance(avaliacao, Replay):
            # Re-renderiza: `garantir_qrcode_vigente` e idempotente, devolve
            # o MESMO QRCode da 1a chamada (UNIQUE hash + revogado_em IS NULL),
            # garantindo PDF deterministico.
            pdf_bytes = gerar_etiqueta_pdf(equipamento)
            return _resposta_pdf_etiqueta(equipamento, pdf_bytes)

        assert isinstance(avaliacao, NovoProcessamento)
        try:
            pdf_bytes = gerar_etiqueta_pdf(equipamento)
        except Exception:
            falhar_chave(
                chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=500,
            )
            raise
        resumo: dict[str, str] = {"equipamento_tag": equipamento.tag}
        concluir_chave(
            chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            response_status=200,
            response_body_resumo=resumo,
        )
        return _resposta_pdf_etiqueta(equipamento, pdf_bytes)


    # authz-check: skip -- RequireAuthz global + ACTION_MAP['ficha360'] = 'equipamentos.ficha360'
    @action(detail=True, methods=["get"], url_path="ficha360")
    def ficha360(self, request: Request, id: str | None = None) -> Response:
        """GET `/equipamentos/{id}/ficha360/?finalidade=executar_os`

        Retorna ficha 360 (T-EQP-024 / AC-EQP-003-1):
        - Dados base + perfil_no_momento_do_cadastro (P-EQP-R1).
        - Versoes (`EquipamentoVersao`).
        - Aprovacoes pendentes (`AprovacaoPendenteEquipamentoVersao`).
        - Certificados (porta stub Marco 2 / Wave A expande).
        - Eventos (`Auditoria` filtrado por equipamento_id).

        INV-013: grava `AcessoDadosCliente` ANTES de renderizar quando
        equipamento tem cliente atual. `finalidade` obrigatoria (enum
        `FinalidadeAcessoCliente` — P-EQP-R7 alinhamento).
        """
        from src.infrastructure.audit.breaker import (
            registrar_acesso_dados_cliente_com_breaker,
        )
        from src.infrastructure.audit.models import FinalidadeAcessoCliente
        from src.infrastructure.equipamentos.services_ficha360 import (
            construir_ficha_360,
        )

        finalidade = request.query_params.get("finalidade", "")
        if finalidade not in FinalidadeAcessoCliente.values:
            return Response(
                {
                    "detail": "finalidade_obrigatoria_e_enum",
                    "validas": list(FinalidadeAcessoCliente.values),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None
        ip_hash = _hashear_ip_request(request, tenant_id)

        # INV-013: log de acesso ANTES de renderizar. cliente_id pode
        # ser None (equipamento sem cliente atual ou orfao_pendente).
        # T-CLI-104 breaker: sobrevive a rollback do request.
        registrar_acesso_dados_cliente_com_breaker(
            tenant_id=tenant_id,
            usuario_id=user_id,
            cliente_id=equipamento.cliente_atual_id,
            finalidade=finalidade,
            recurso={
                "equipamento_id": str(equipamento.id),
                "tipo": "equipamento_ficha360",
            },
            ip_hash=ip_hash,
        )

        ficha = construir_ficha_360(equipamento)
        return Response(ficha, status=status.HTTP_200_OK)


    # authz-check: skip -- RequireAuthz global + ACTION_MAP['transferir'] = 'equipamentos.transferir'
    @action(detail=True, methods=["post"], url_path="transferir")
    def transferir(self, request: Request, id: str | None = None) -> Response:
        """POST `/equipamentos/{id}/transferir/` — US-EQP-004 (T-EQP-034..040).

        Body:
        ```
        {
          "cessionario_cliente_id": "uuid",
          "motivo_categoria": "venda|comodato|doacao|correcao_cadastral|outro",
          "motivo_detalhe": "string (obrigatorio se outro)",
          "aceite_cedente": {
            "tipo": "presencial_atendente|contrato_fisico_digitalizado|portal_cliente_otp",
            "usuario_id_atendente": "uuid",
            "observacao": "string",
            "consentimento_historico_expresso": true|false
          },
          "aceite_cessionario": {... mesmo schema ...}
        }
        ```

        Codigos:
        - 200 OK + `{transferencia_id, status, foi_efetivada}` quando
          ambos aceites validos -> EFETIVADA.
        - 201 Created + `{transferencia_id, status="pendente"}` quando
          0 ou 1 aceite -> PENDENTE (Wave A: endpoint de aceite tardio).
        - 412 + `{detail, lado, motivo}` quando cedente/cessionario
          bloqueado (INV-INT-010 — Marco 1 predicate).
        - 422 + `{detail: "cliente nao encontrado neste tenant"}` quando
          cessionario cross-tenant (INV-050 — sem oracle).
        - 400 + `{detail}` outros erros de validacao.
        """
        from uuid import UUID as _UUID

        from .services_transferencia import (
            Aceite,
            CessionarioCrossTenant,
            CessionarioIgualCedente,
            ClienteBloqueado,
            DadosSolicitacaoTransferencia,
            MotivoDetalheObrigatorio,
            TransferenciaInvalida,
            solicitar_transferencia,
        )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        try:
            cessionario_id = _UUID(str(body.get("cessionario_cliente_id", "")))
        except (ValueError, TypeError):
            return Response(
                {"detail": "cessionario_cliente_id_invalido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # T-EQP-037: Idempotency-Key obrigatorio (reusa horizontal F-A).
        chave_header = request.META.get("HTTP_IDEMPOTENCY_KEY")
        avaliacao_idem = avaliar_chave_idempotencia(
            tenant_id=tenant_id,
            usuario_id=user_id,
            endpoint=ENDPOINT_TRANSFERIR,
            chave_header=chave_header,
            payload={
                "equipamento_id": str(equipamento.id),
                "cessionario_cliente_id": str(cessionario_id),
                "motivo_categoria": str(body.get("motivo_categoria", "")),
            },
        )
        if isinstance(avaliacao_idem, ErroValidacao):
            return _resposta_erro_idempotencia(avaliacao_idem)
        if isinstance(avaliacao_idem, Replay):
            # Replay determinístico: devolve o transferencia_id da 1a
            # chamada via resumo persistido (politica P-EQP-T6).
            resumo = avaliacao_idem.response_body_resumo or {}
            return Response(resumo, status=status.HTTP_200_OK)
        assert isinstance(avaliacao_idem, NovoProcessamento)

        def _parse_aceite(payload: dict | None) -> Aceite | None:
            if not payload:
                return None
            try:
                return Aceite(
                    tipo=str(payload.get("tipo", "")),
                    usuario_id_atendente=_UUID(
                        str(payload.get("usuario_id_atendente", ""))
                    ),
                    observacao=str(payload.get("observacao", "")),
                    consentimento_historico_expresso=bool(
                        payload.get("consentimento_historico_expresso", False)
                    ),
                    nivel_consentimento_historico=str(
                        payload.get("nivel_consentimento_historico", "")
                    ),
                )
            except (ValueError, TypeError):
                return None

        dados = DadosSolicitacaoTransferencia(
            cessionario_cliente_id=cessionario_id,
            motivo_categoria=str(body.get("motivo_categoria", "")),
            motivo_detalhe=str(body.get("motivo_detalhe", "")),
            aceite_cedente=_parse_aceite(body.get("aceite_cedente")),
            aceite_cessionario=_parse_aceite(body.get("aceite_cessionario")),
            texto_termo_versao_id=str(
                body.get("texto_termo_versao_id", "v1.0-2026-05-22")
            ),
        )

        try:
            resultado = solicitar_transferencia(
                tenant_id=tenant_id,
                equipamento=equipamento,
                solicitado_por_id=user_id,
                dados=dados,
            )
        except CessionarioCrossTenant as exc:
            falhar_chave(
                chave_id=avaliacao_idem.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=422,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except ClienteBloqueado as exc:
            falhar_chave(
                chave_id=avaliacao_idem.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=412,
            )
            return Response(
                {
                    "detail": "cliente_bloqueado",
                    "lado": exc.lado,
                    "motivo": exc.motivo,
                },
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        except (
            CessionarioIgualCedente,
            MotivoDetalheObrigatorio,
            TransferenciaInvalida,
        ) as exc:
            falhar_chave(
                chave_id=avaliacao_idem.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=400,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_http = (
            status.HTTP_200_OK if resultado.foi_efetivada else status.HTTP_201_CREATED
        )
        resumo = {
            "transferencia_id": str(resultado.transferencia.id),
            "status": resultado.transferencia.status,
            "foi_efetivada": resultado.foi_efetivada,
        }
        concluir_chave(
            chave_id=avaliacao_idem.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            response_status=status_http,
            response_body_resumo=resumo,
        )
        return Response(resumo, status=status_http)


    # authz-check: skip -- RequireAuthz global + ACTION_MAP['revogar_consentimento_historico']
    @action(
        detail=True,
        methods=["post"],
        url_path="consentimento-historico/revogar",
    )
    def revogar_consentimento_historico(
        self, request: Request, id: str | None = None
    ) -> Response:
        """POST `/equipamentos/{id}/consentimento-historico/revogar/` — T-EQP-041.

        Body:
        ```
        {
          "consentimento_id": "uuid?",           // se omitido pega o ativo
          "justificativa": "string >=30 + anti-PII",
          "via_revogacao": "presencial_atendente|contrato_fisico_digitalizado|portal_cliente_otp"
        }
        ```

        Codigos:
        - 200 OK + `{consentimento_id, revogado_em}` — revogado.
        - 400 + `{detail}` — validacao (justificativa curta/PII, via invalida).
        - 404 — consentimento nao encontrado neste equipamento/tenant.
        - 412 + `{detail}` — consentimento ja revogado (one-shot).
        """
        from uuid import UUID as _UUID

        from src.infrastructure.equipamentos.models import (
            ConsentimentoHistoricoEquipamento,
        )
        from src.infrastructure.equipamentos.services_consentimento_historico import (
            ConsentimentoInvalido,
            ConsentimentoJaRevogado,
            JustificativaInvalida,
            revogar_consentimento_historico,
        )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        consent_id_raw = body.get("consentimento_id")
        justificativa = str(body.get("justificativa", ""))
        via_revogacao = str(body.get("via_revogacao", ""))

        qs = ConsentimentoHistoricoEquipamento.objects.filter(
            tenant_id=tenant_id,
            equipamento_id=equipamento.id,
        )
        if consent_id_raw:
            try:
                consent_id = _UUID(str(consent_id_raw))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "consentimento_id_invalido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            consentimento = qs.filter(id=consent_id).first()
        else:
            # Default: ativo (nao revogado) mais recente.
            consentimento = qs.filter(revogado_em__isnull=True).order_by(
                "-concedido_em"
            ).first()

        if consentimento is None:
            return Response(
                {"detail": "consentimento_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            resultado = revogar_consentimento_historico(
                tenant_id=tenant_id,
                consentimento=consentimento,
                revogado_por_id=user_id,
                justificativa=justificativa,
                via_revogacao=via_revogacao,
            )
        except ConsentimentoJaRevogado as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        except (JustificativaInvalida, ConsentimentoInvalido) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "consentimento_id": str(resultado.consentimento.id),
                "revogado_em": resultado.consentimento.revogado_em.isoformat(),
                "nivel": resultado.consentimento.nivel,
            },
            status=status.HTTP_200_OK,
        )


    # authz-check: skip -- RequireAuthz global + ACTION_MAP['sucatear'] = 'equipamentos.sucatear'
    @action(detail=True, methods=["post"], url_path="sucatear")
    def sucatear(
        self, request: Request, id: str | None = None
    ) -> Response:
        """POST `/equipamentos/{id}/sucatear/` — US-EQP-005 (T-EQP-042+043+046).

        Body:
        ```
        {
          "justificativa": ">=30 chars + anti-PII",
          "confirmacao_dupla": bool,
          "ciencia_validade_tecnica_registrada": bool,
          "texto_modal_versao_id": "v1.0-2026-05-23"  // opcional
        }
        ```

        Codigos:
        - 200 OK + `{sucatamento_id, tem_cert_vigente_no_momento, status}`.
        - 400 + `{detail}` — validacao (justificativa curta/PII).
        - 422 + `{detail, codigo, texto_modal}` — cert vigente sem
          `confirmacao_dupla=True` E `ciencia_validade_tecnica_registrada=True`.
        - 409 + `{detail}` — sucatamento duplicado ou transicao status
          invalida.
        """
        from src.infrastructure.equipamentos.services_sucatamento import (
            CertVigenteSemConfirmacaoDupla,
            DadosSucatamento,
            JustificativaInvalida,
            StatusInvalido,
            SucatamentoDuplicado,
            SucatamentoInvalido,
            sucatear_equipamento,
        )
        from src.infrastructure.equipamentos.validators import (
            TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE,
            TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA,
        )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        dados = DadosSucatamento(
            justificativa=str(body.get("justificativa", "")),
            confirmacao_dupla=bool(body.get("confirmacao_dupla", False)),
            ciencia_validade_tecnica_registrada=bool(
                body.get("ciencia_validade_tecnica_registrada", False)
            ),
            texto_modal_versao_id=str(
                body.get(
                    "texto_modal_versao_id",
                    TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA,
                )
            ),
        )

        try:
            resultado = sucatear_equipamento(
                tenant_id=tenant_id,
                equipamento=equipamento,
                sucateado_por_id=user_id,
                dados=dados,
            )
        except CertVigenteSemConfirmacaoDupla as exc:
            return Response(
                {
                    "detail": str(exc),
                    "codigo": "cert_vigente_exige_confirmacao_dupla",
                    "texto_modal": TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE,
                    "texto_modal_versao_id": (
                        TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA
                    ),
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except (SucatamentoDuplicado, StatusInvalido) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except (JustificativaInvalida, SucatamentoInvalido) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "sucatamento_id": str(resultado.sucatamento.id),
                "tem_cert_vigente_no_momento": (
                    resultado.tem_cert_vigente_no_momento
                ),
                "status": "sucata",
            },
            status=status.HTTP_200_OK,
        )


    # authz-check: skip -- RequireAuthz global + ACTION_MAP['receber'] = 'equipamentos.receber'
    @action(detail=True, methods=["post"], url_path="recebimentos")
    def receber(
        self, request: Request, id: str | None = None
    ) -> Response:
        """POST `/equipamentos/{id}/recebimentos/` — US-EQP-006 (T-EQP-047+052).

        Aceita multipart-form (foto opcional Marco 2) OU JSON:
        ```
        {
          "condicao_visual_chegada": "integro|amassado|lacre_violado|...",
          "anomalias_observadas": "string <=500 + anti-PII",
          "decisao_apos_anomalia": "prosseguir|contatar_cliente_aguardando|...",  // se !integro
          "justificativa_decisao": "string >=30 + anti-PII",  // se !integro
        }
        ```
        + `foto` (multipart-form key) opcional.

        Codigos: 200 OK + `{recebimento_id, status_fluxo_lab, foto_sha256?}`,
        400/422 validacao, 403 sem authz.
        """
        from src.infrastructure.equipamentos.services_foto_storage import (
            FotoInvalida,
        )
        from src.infrastructure.equipamentos.services_recebimento import (
            AnomaliaSemDecisao,
            AnomaliasObservadasInvalidas,
            CondicaoInvalida,
            DadosRecebimento,
            DecisaoInvalida,
            RecebimentoInvalido,
            criar_recebimento,
        )
        from src.infrastructure.equipamentos.services_recebimento import (
            JustificativaInvalida as JustifInv,
        )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        foto_arquivo = request.FILES.get("foto") if request.FILES else None
        foto_bytes = foto_arquivo.read() if foto_arquivo is not None else None
        foto_mime = (
            foto_arquivo.content_type if foto_arquivo is not None else ""
        )

        dados = DadosRecebimento(
            condicao_visual_chegada=str(body.get("condicao_visual_chegada", "")),
            anomalias_observadas=str(body.get("anomalias_observadas", "")),
            decisao_apos_anomalia=str(body.get("decisao_apos_anomalia", "")),
            justificativa_decisao=str(body.get("justificativa_decisao", "")),
            foto_bytes=foto_bytes,
            foto_mime_type=foto_mime,
        )

        try:
            resultado = criar_recebimento(
                tenant_id=tenant_id,
                equipamento=equipamento,
                recebido_por_id=user_id,
                dados=dados,
            )
        except (
            CondicaoInvalida,
            DecisaoInvalida,
            AnomaliaSemDecisao,
            AnomaliasObservadasInvalidas,
            JustifInv,
        ) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except FotoInvalida as exc:
            return Response(
                {"detail": str(exc), "codigo": "foto_invalida"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RecebimentoInvalido as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "recebimento_id": str(resultado.recebimento.id),
                "status_fluxo_lab": resultado.recebimento.status_fluxo_lab,
                "foto_storage_key": resultado.foto_storage_key,
                "foto_sha256": resultado.foto_sha256,
            },
            status=status.HTTP_200_OK,
        )

    # authz-check: skip -- RequireAuthz global + ACTION_MAP['transicionar_recebimento']
    @action(
        detail=True,
        methods=["post"],
        url_path=(
            r"recebimentos/(?P<rec_id>[0-9a-f-]{36})/transicionar"
        ),
    )
    def transicionar_recebimento(
        self,
        request: Request,
        id: str | None = None,
        rec_id: str | None = None,
    ) -> Response:
        """POST `/equipamentos/{id}/recebimentos/{rec_id}/transicionar/` —
        T-EQP-050.

        Body: `{"status_alvo": "em_inspecao_visual", "observacao": ""}`.

        Codigos: 200 OK / 404 nao encontrado / 409 transicao invalida /
        400 status_alvo fora enum / 403 sem authz.
        """
        from uuid import UUID as _UUID

        from src.infrastructure.equipamentos.models import (
            EquipamentoRecebimento,
        )
        from src.infrastructure.equipamentos.services_recebimento import (
            TransicaoStatusFluxoLabInvalida,
            transicionar_status_fluxo_lab,
        )

        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        try:
            rec_uuid = _UUID(str(rec_id))
        except (ValueError, TypeError):
            return Response(
                {"detail": "rec_id_invalido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recebimento = (
            EquipamentoRecebimento.objects.filter(
                id=rec_uuid,
                tenant_id=tenant_id,
                equipamento_id=equipamento.id,
            ).first()
        )
        if recebimento is None:
            return Response(
                {"detail": "recebimento_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        body = request.data or {}
        status_alvo = str(body.get("status_alvo", ""))
        observacao = str(body.get("observacao", ""))

        try:
            resultado = transicionar_status_fluxo_lab(
                tenant_id=tenant_id,
                recebimento=recebimento,
                status_alvo=status_alvo,
                transicionado_por_id=user_id,
                observacao=observacao,
            )
        except TransicaoStatusFluxoLabInvalida as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "recebimento_id": str(resultado.recebimento.id),
                "status_fluxo_lab": resultado.recebimento.status_fluxo_lab,
            },
            status=status.HTTP_200_OK,
        )


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    """Converte `ErroValidacao` em DRF Response com headers opcionais."""
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    response = Response(body, status=erro.http_status)
    if erro.headers:
        for nome, valor in erro.headers.items():
            response[nome] = valor
    return response
