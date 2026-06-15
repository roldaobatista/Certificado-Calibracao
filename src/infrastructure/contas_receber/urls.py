"""URL routing da frente contas-receber (T-CR-035 / T-CR-036).

ContasReceberViewSet via DefaultRouter (`contas-receber`). Plugado em
config/urls.py raiz.

Rota adicional (Fatia 2b):
  POST /api/v1/public/contas-receber/webhook/ — webhook gateway público (T-CR-036).
  Middleware allowlist: `/api/v1/public/contas-receber/` em multitenant/middleware.py.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ContasReceberViewSet
from .views_webhook import contas_receber_webhook_view

router = DefaultRouter()
router.register("contas-receber", ContasReceberViewSet, basename="contas-receber")

urlpatterns = [
    *router.urls,
    # T-CR-036: endpoint público de webhook (sem auth — HMAC = autorização)
    path(
        "public/contas-receber/webhook/",
        contas_receber_webhook_view,
        name="contas-receber-webhook",
    ),
]
