from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone as django_timezone
import requests
from datetime import  datetime, timedelta, timezone


from api.azure_ai import AzureDocumentTranslator, AzurePIIRedaction
from api.models import LanguageCode, Profile, RedactionJob, TranslationJob
from api.serializers import LanguageCodeSerializer, RedactionJobSerializer, TranslationJobSerializer

SAS_TTL_MINUTES = 60


# Create your views here.
class TranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = TranslationJobSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'profile_id': self.request.user.id}
    
    def get_queryset(self):
        user = self.request.user
        day_start = django_timezone.now() - timedelta(days=1)
        if user.is_staff:
            return TranslationJob.objects.filter(created_at__gte=day_start).order_by("-created_at")
        profile_id = Profile.objects.only("id").get(user_id=user.id)
        return TranslationJob.objects.filter(profile_id=profile_id, created_at__gte=day_start).order_by("-created_at")
  
    
    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        target_lang = request.data.get('target_lang')
        if not file or not target_lang:
            return Response({"error": "File and target_lang are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        az = AzureDocumentTranslator()
        filename = file.name
        
        with transaction.atomic():
            source_blob_url, target_blob_url, operation_location = az.translate_single_doument(file, filename, target_lang)
            job = TranslationJob.objects.create(
                filename=filename,
                target_lang=target_lang,
                source_blob_url=source_blob_url,
                target_container_url=target_blob_url, 
                status="notStarted",
                operation_location=operation_location,
                profile=request.user.profile
            )
        return Response(TranslationJobSerializer(job).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def list_blobs(self, request):
        az = AzureDocumentTranslator()
        blobs = az.get_all_blobs_in_container('document-out')
        return Response({"blobs": blobs}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        job = self.get_object()
        az = AzureDocumentTranslator()

        # No jumping back in status - useful for UI display
        progress_order = ["notStarted", "running", "succeeded", "failed", "canceled"]
        def is_monotone(old_status, new_status):
            try:
                return progress_order.index(new_status) >= progress_order.index(old_status)
            except ValueError:
                return False
            
        try:
            op = az.get_operation_status(job.operation_location)
            azure_status = (op.get('status') or '').lower()
            mapped = {
                "notstarted": "notStarted",
                "running": "running",
                "cancelling": "running",
                "succeeded": "succeeded",
                "failed": "failed",
                "cancelled": "canceled"
            }.get(azure_status, job.status)

            if is_monotone(job.status, mapped):
                job.status = mapped
                
                # Generate SAS only once when first succeeded and not already existing
                if job.status == "succeeded" and not job.download_url:
                    az = AzureDocumentTranslator()
                    job.download_url, job.download_expires_at = az.build_sas_url(job.target_container_url, minutes_valid=SAS_TTL_MINUTES)
            job.save()
            data = TranslationJobSerializer(job).data
            return Response(data, status=status.HTTP_200_OK)
        
        except requests.HTTPError as e:
            job.status = "failed"
            job.error_message = f"Azure polling error: {str(e)}"
            job.save()
            return Response(TranslationJobSerializer(job).data, status=status.HTTP_200_OK)
        

class LanguageCodeViewSet(ListModelMixin, GenericViewSet):
    queryset = LanguageCode.objects.all().order_by('name')
    serializer_class = LanguageCodeSerializer
    permission_classes = [IsAuthenticated]


class PIIRedactionViewSet(viewsets.ModelViewSet):
    serializer_class = RedactionJobSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        day_start = django_timezone.now() - timedelta(days=1)
        if user.is_staff:
            return RedactionJob.objects.filter(created_at__gte=day_start).order_by("-created_at")
        profile_id = Profile.objects.only("id").get(user_id=user.id)
        return RedactionJob.objects.filter(profile_id=profile_id, created_at__gte=day_start).order_by("-created_at")
    
    
    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        document_lang = request.data.get('document_lang') # In Frontend we have to make sure this is provided
        if not file or not document_lang:
            return Response({"error": "File and document_lang are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        az = AzurePIIRedaction()
        filename = file.name

        with transaction.atomic():
            source_blob_url, operation_location = az.perform_redaction(file, filename, document_lang)
            job = RedactionJob.objects.create(
                filename=filename,
                source_blob_url=source_blob_url,
                status="notStarted",
                operation_location=operation_location,
                profile=request.user.profile
            )
        return Response(RedactionJobSerializer(job).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        job = self.get_object()
        az = AzurePIIRedaction()

        # No jumping back in status - useful for UI display
        progress_order = ["notStarted", "running", "succeeded", "failed", "canceled"]
        def is_monotone(old_status, new_status):
            try:
                return progress_order.index(new_status) >= progress_order.index(old_status)
            except ValueError:
                return False
            
        try:
            op = az.get_operation_status(job.operation_location)
            azure_status = (op.get('status') or '').lower()
            mapped = {
                "notstarted": "notStarted",
                "running": "running",
                "cancelling": "running",
                "succeeded": "succeeded",
                "failed": "failed",
                "cancelled": "canceled"
            }.get(azure_status, job.status)

            if is_monotone(job.status, mapped):
                job.status = mapped
                
                # Generate SAS only once when first succeeded and not already existing
                if job.status == "succeeded" and not job.download_url:
                    target_blob_url = az.get_target_blob_url(op)
                    job.target_blob_url = target_blob_url
                    job.download_url, job.download_expires_at = az.build_sas_url(job.target_blob_url, minutes_valid=SAS_TTL_MINUTES)
            job.save()
            data = RedactionJobSerializer(job).data
            return Response(data, status=status.HTTP_200_OK)
        
        except requests.HTTPError as e:
            job.status = "failed"
            job.error_message = f"Azure polling error: {str(e)}"
            job.save()
            return Response(RedactionJobSerializer(job).data, status=status.HTTP_200_OK)

