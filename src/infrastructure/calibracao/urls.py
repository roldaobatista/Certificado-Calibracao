"""URL routing M4 P4 Fase 8 (T-CAL-123..127 + 135).

Registros:
  - calibracoes (CalibracaoViewSet) — recepcionar/configurar/cancelar (T-CAL-123)
  - LeituraViewSet (T-CAL-124) — registrar-leitura + corrigir
  - RevisaoViewSet (T-CAL-126) — aprovar-revisao + rejeitar-revisao
  - ConferenciaViewSet (T-CAL-127) — aprovar-2a-conferencia

ViewSets de Leitura/Revisao/Conferencia usam url_path absoluto em cada
@action (calibracoes/{pk}/<acao>) — nao registrados via DefaultRouter
pra evitar prefixo extra.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CalibracaoViewSet,
    ConferenciaViewSet,
    LeituraViewSet,
    NaoConformidadeViewSet,
    OrcamentoIncertezaViewSet,
    ReclamacaoViewSet,
    RevisaoViewSet,
    SubcontratacaoViewSet,
)

router = DefaultRouter()
router.register("calibracoes", CalibracaoViewSet, basename="calibracao")

urlpatterns = [
    *router.urls,
    # T-CAL-124 LeituraViewSet
    path(
        "calibracoes/<str:calibracao_pk>/registrar-leitura/",
        LeituraViewSet.as_view({"post": "registrar"}),
        name="calibracao-registrar-leitura",
    ),
    path(
        "leituras/<str:leitura_pk>/corrigir/",
        LeituraViewSet.as_view({"post": "corrigir"}),
        name="leitura-corrigir",
    ),
    # T-CAL-126 RevisaoViewSet
    path(
        "calibracoes/<str:calibracao_pk>/aprovar-revisao/",
        RevisaoViewSet.as_view({"post": "aprovar"}),
        name="calibracao-aprovar-revisao",
    ),
    path(
        "calibracoes/<str:calibracao_pk>/rejeitar-revisao/",
        RevisaoViewSet.as_view({"post": "rejeitar"}),
        name="calibracao-rejeitar-revisao",
    ),
    # T-CAL-127 ConferenciaViewSet
    path(
        "calibracoes/<str:calibracao_pk>/aprovar-2a-conferencia/",
        ConferenciaViewSet.as_view({"post": "aprovar_2a"}),
        name="calibracao-aprovar-2a-conferencia",
    ),
    # T-CAL-128 NaoConformidadeViewSet
    path(
        "nao-conformidades/abrir/",
        NaoConformidadeViewSet.as_view({"post": "abrir"}),
        name="nao-conformidade-abrir",
    ),
    path(
        "nao-conformidades/<str:nc_pk>/fechar/",
        NaoConformidadeViewSet.as_view({"post": "fechar"}),
        name="nao-conformidade-fechar",
    ),
    # T-CAL-132 ReclamacaoViewSet
    path(
        "reclamacoes/abrir/",
        ReclamacaoViewSet.as_view({"post": "abrir"}),
        name="reclamacao-abrir",
    ),
    path(
        "reclamacoes/<str:reclamacao_pk>/atribuir-rt/",
        ReclamacaoViewSet.as_view({"post": "atribuir_rt"}),
        name="reclamacao-atribuir-rt",
    ),
    path(
        "reclamacoes/<str:reclamacao_pk>/responder/",
        ReclamacaoViewSet.as_view({"post": "responder"}),
        name="reclamacao-responder",
    ),
    # T-CAL-129 SubcontratacaoViewSet (US-CAL-017 cl. 6.6)
    path(
        "calibracoes/<str:calibracao_pk>/subcontratar/",
        SubcontratacaoViewSet.as_view({"post": "subcontratar"}),
        name="calibracao-subcontratar",
    ),
    path(
        "calibracoes/<str:calibracao_pk>/registrar-recebimento-subcontratado/",
        SubcontratacaoViewSet.as_view({"post": "registrar_recebimento"}),
        name="calibracao-registrar-recebimento-subcontratado",
    ),
    # T-CAL-125 OrcamentoIncertezaViewSet (US-CAL-005 + US-CAL-006)
    path(
        "calibracoes/<str:calibracao_pk>/calcular-incerteza/",
        OrcamentoIncertezaViewSet.as_view({"post": "calcular_incerteza"}),
        name="calibracao-calcular-incerteza",
    ),
    path(
        "calibracoes/<str:calibracao_pk>/avaliar-conformidade/",
        OrcamentoIncertezaViewSet.as_view({"post": "avaliar_conformidade"}),
        name="calibracao-avaliar-conformidade",
    ),
]
