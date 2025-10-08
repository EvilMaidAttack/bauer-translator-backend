# app/models.py
import uuid
from django.db import models

class TranslationJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=256)
    target_lang = models.CharField(max_length=16)
    source_blob_url = models.URLField(max_length=2048)
    target_container_url = models.URLField(max_length=2048)  
    operation_location = models.URLField(max_length=2048)    
    status = models.CharField(max_length=32, default="notStarted")  # notStarted|running|succeeded|failed|canceled
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
