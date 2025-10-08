from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import TranslationJobViewSet

router = DefaultRouter()
router.register(r'translate', TranslationJobViewSet, basename='translate')

urlpatterns = [
    path('', include(router.urls)),
]