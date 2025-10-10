from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import TranslationJobViewSet, LanguageCodeViewSet

router = DefaultRouter()
router.register(r'translate', TranslationJobViewSet, basename='translate')
router.register(r'languages', LanguageCodeViewSet, basename='languages')

urlpatterns = [
    path('', include(router.urls)),
]