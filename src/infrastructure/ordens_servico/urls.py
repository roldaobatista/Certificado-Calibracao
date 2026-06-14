"""URL routing M3 OS Fase 8 (T-OS-094..104).

T-OSME-035 (ADR-0082): ItemComercialOSViewSet expoe CRUD minimo de
itens comerciais por OS (acao authz os.gerir_item_comercial).
"""

from rest_framework.routers import DefaultRouter

from .views import AtividadeViewSet, OSViewSet
from .views_item_comercial import ItemComercialOSViewSet

router = DefaultRouter()
router.register("os", OSViewSet, basename="os")
router.register("atividades", AtividadeViewSet, basename="atividade")
# T-OSME-035: ViewSet de itens comerciais — endpoints montados como @action
# url_path customizado (os/{os_id}/itens-comerciais) no proprio ViewSet.
router.register("item-comercial-os", ItemComercialOSViewSet, basename="item-comercial-os")

urlpatterns = [
    *router.urls,
]
