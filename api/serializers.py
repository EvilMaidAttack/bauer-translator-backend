from datetime import  datetime, timedelta, timezone
from django.conf import settings
from rest_framework import serializers
from urllib.parse import urlsplit

from api.azure_translate import AzureDocumentTranslator
from api.models import LanguageCode, TranslationJob 

SAS_TTL_MINUTES = 60 

def normalize_target(code: str) -> str:
    return code.lower() if code else code

class TranslationJobSerializer(serializers.ModelSerializer):    
    download_url = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    download_expires_at = serializers.SerializerMethodField()            
    
    class Meta:
        model = TranslationJob
        fields = ['id', 'filename', 'target_lang', 'source_blob_url', 'target_container_url',
                    'operation_location', 'status', 'error_message', 'created_at', 'updated_at',
                    'download_url', 'display_status', 'target_name', 'profile',
                    'download_expires_at']
        read_only_fields = ['id', 'source_blob_url', 'target_container_url', 'operation_location', 
                            'status', 'error_message', 'created_at', 'updated_at', 'download_url',
                            'display_status', 'target_name', 'profile', 'download_expires_at']
        
    
    def get_download_url(self, obj):
        if obj.status != "succeeded":
            return None
        az = AzureDocumentTranslator()
        return az.build_sas_url(obj.target_container_url, minutes_valid=SAS_TTL_MINUTES)
    

    def get_display_status(self, obj):
        status_map = {
            "notStarted": "Queued",
            "running": "In Progress",
            "succeeded": "Completed",
            "failed": "Failed",
            "canceled": "Canceled"
        }
        return status_map.get(obj.status, obj.status)
    
    def get_target_name(self, obj):
        return obj.target_container_url.rsplit('/', 1)[-1]
    
    def get_download_expires_at(self, obj):
        if obj.status != "succeeded":
            return None
        return (datetime.now(timezone.utc) + timedelta(minutes=SAS_TTL_MINUTES)).isoformat()


class LanguageCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageCode
        fields = ['id', 'code', 'name']
        read_only_fields = ['id', 'code', 'name']