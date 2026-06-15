"""URL routing da frente contas-receber (T-CR-035).

ContasReceberViewSet via DefaultRouter (`contas-receber`). Plugado em
config/urls.py raiz.
"""

from rest_framework.routers import DefaultRouter

from .views import ContasReceberViewSet

router = DefaultRouter()
router.register("contas-receber", ContasReceberViewSet, basename="contas-receber")

urlpatterns = [
    *router.urls,
]
