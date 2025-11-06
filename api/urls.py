from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import TranslationJobViewSet, LanguageCodeViewSet, PIIRedactionViewSet

router = DefaultRouter()
router.register(r'translate', TranslationJobViewSet, basename='translate')
router.register(r'languages', LanguageCodeViewSet, basename='languages')
router.register(r'redact', PIIRedactionViewSet, basename='redact')

urlpatterns = [
    path('', include(router.urls)),
]