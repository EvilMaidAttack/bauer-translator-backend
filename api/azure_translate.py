from urllib.parse import urlsplit
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone
import requests
load_dotenv(override=True)

# TODO: Translation fails when target_document blob already exists in document-out container => Find a fix

class AzureDocumentTranslator():
    def __init__(self):
        self.endpoint = os.getenv('AZURE_TRANSLATION_ENDPOINT')
        self.key = os.getenv('AZURE_TRANSLATION_KEY')
        self.container_in = os.getenv('AZURE_BLOB_CONTAINER_IN')
        self.container_out = os.getenv('AZURE_BLOB_CONTAINER_OUT')
        self.account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        self.storage_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    
    def translate_single_doument(self, file, file_name: str, target_lang: str):
        print("Uploading to Azure Blob Storage...")
        source_file = self.__upload_to_blob(file, file_name)
        print(f"Uploaded to blob {source_file}")
        
        parts = urlsplit(source_file)
        target_lang = self.__normalize_target(target_lang)
        stem, ext = os.path.splitext(file_name)
        target_file = f"{parts.scheme}://{parts.netloc}/{self.container_out}/{stem}_{target_lang}{ext}"
        
        request_url = f"{self.endpoint}translator/text/batch/v1.1/batches"
        headers = {'Ocp-Apim-Subscription-Key': self.key}
        payload = self.__get_payload(source_file, target_file, target_lang)
        print("Requesting document translation...")
        response = requests.post(request_url, headers=headers, json=payload)
        response.raise_for_status()
        operation_location = response.headers["operation-location"]
        print(f"Translation job scheduled. Operation location: {operation_location}")
        return source_file, target_file, operation_location
    
    def get_all_blobs_in_container(self, container_name):
        blob_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_ACCOUNT_CONNECTION_STRING'))
        container_client = blob_client.get_container_client(container_name)
        blobs = container_client.list_blobs()
        return [blob.name for blob in blobs]
    
    def get_operation_status(self, operation_location: str) -> dict:
        headers = {'Ocp-Apim-Subscription-Key': self.key}
        response = requests.get(operation_location, headers=headers)
        response.raise_for_status()
        print(f"Debug info: Operation status response: {response.json()}")
        return response.json()
    
    def build_sas_url(self, blob_url:str, minutes_valid: int = 60) -> tuple[str, datetime]:
        parts = urlsplit(blob_url)
        path = parts.path.lstrip('/')
        container, blob_name = path.split('/', 1)
        expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes_valid)
        sas = generate_blob_sas(
            account_name=self.account_name,
            container_name=container,
            blob_name=blob_name,
            account_key=self.storage_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry
        )
        sas_url = f"{parts.scheme}://{parts.netloc}/{container}/{blob_name}?{sas}"
        #print(f"SAS URL: {sas_url} - EXPIRES at {expiry}")
        return sas_url, expiry
            
        
    
    def __upload_to_blob(self, file, name) -> str:
        blob_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_ACCOUNT_CONNECTION_STRING'))
        container_client = blob_client.get_container_client(self.container_in)
        blob = container_client.upload_blob(name = name, data = file, overwrite = True)  
        return blob.url
    
    def __normalize_target(self, code: str) -> str:
        return code.lower() if code else code
    
    def __get_payload(self, source_file: str, target_file: str, target_lang: str) -> dict:
        return {
            "inputs": [
                {
                    "storageType": "File",
                    "source": {
                        "sourceUrl": source_file
                    },
                    "targets": [
                        {
                            "targetUrl": target_file,
                            "language": target_lang
                        }
                    ]
                }
            ]
        }
        
        
        



