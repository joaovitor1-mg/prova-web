from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FilaAdminViewSet,
    PainelPublicoAPIView,
    login_usuario_view,
    logout_usuario_view,
    painel_view,
    recepcao_view,
)

router = DefaultRouter()
router.register(r'fila', FilaAdminViewSet, basename='fila-admin')

urlpatterns = [
    # APIs REST
    path('api/painel/', PainelPublicoAPIView.as_view(), name='api-painel'),
    path('api/', include(router.urls)),

    # Páginas Web
    path('', painel_view, name='home'),
    path('painel/', painel_view, name='painel_view'),
    path('recepcao/', recepcao_view, name='recepcao_view'),
    path('login/', login_usuario_view, name='login_view'),
    path('logout/', logout_usuario_view, name='logout_view'),
]
