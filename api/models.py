# app/models.py
import uuid
from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True, related_name="profile")
    def __str__(self):
        return self.user.email

class TranslationJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="jobs")
    filename = models.CharField(max_length=256)
    target_lang = models.CharField(max_length=16)
    source_blob_url = models.URLField(max_length=2048)
    target_container_url = models.URLField(max_length=2048)  
    operation_location = models.URLField(max_length=2048)    
    status = models.CharField(max_length=32, default="notStarted")  # notStarted|running|succeeded|failed|canceled
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_url = models.URLField(max_length=2048, blank=True, default="")
    download_expires_at = models.DateTimeField(null=True, blank=True)

    

class LanguageCode(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)

class RedactionJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="redaction_jobs")
    filename = models.CharField(max_length=256)
    source_blob_url = models.URLField(max_length=2048)
    target_blob_url = models.URLField(max_length=2048, null=True, blank=True)  
    operation_location = models.URLField(max_length=2048) 
    status = models.CharField(max_length=32, default="notStarted")  # notStarted|running|succeeded|failed|canceled
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_url = models.URLField(max_length=2048, blank=True, default="")
    download_expires_at = models.DateTimeField(null=True, blank=True)
    entity_download_url = models.URLField(max_length=2048, blank=True, default="")
    entity_expires_at = models.DateTimeField(null=True, blank=True)

    
