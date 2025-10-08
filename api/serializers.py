from django.conf import settings
from rest_framework import serializers

from api.models import TranslationJob 

def normalize_target(code: str) -> str:
    return code.lower() if code else code

class TranslationJobSerializer(serializers.ModelSerializer):    
    class Meta:
        model = TranslationJob
        fields = ['id', 'filename', 'target_lang', 'source_blob_url', 'target_container_url', 'operation_location', 'status', 'error_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'source_blob_url', 'target_container_url', 'operation_location', 'status', 'error_message', 'created_at', 'updated_at']