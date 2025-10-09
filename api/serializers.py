from django.conf import settings
from rest_framework import serializers

from api.azure_translate import AzureDocumentTranslator
from api.models import TranslationJob 

def normalize_target(code: str) -> str:
    return code.lower() if code else code

class TranslationJobSerializer(serializers.ModelSerializer):    
    download_url = serializers.SerializerMethodField()
    class Meta:
        model = TranslationJob
        fields = ['id', 'filename', 'target_lang', 'source_blob_url', 'target_container_url', 'operation_location', 'status', 'error_message', 'created_at', 'updated_at', 'download_url']
        read_only_fields = ['id', 'source_blob_url', 'target_container_url', 'operation_location', 'status', 'error_message', 'created_at', 'updated_at', 'download_url']
    
    def get_download_url(self, obj):
        if obj.status != "succeeded":
            return None
        az = AzureDocumentTranslator()
        return az.build_sas_url(obj.target_container_url, minutes_valid=60)