import os
import oci
from oci.object_storage import ObjectStorageClient

class ObjectStorageManager:
    def __init__(self):
        self.CONFIG = oci.config.from_file(file_location=os.getenv("config"), profile_name="DEFAULT")
        self.NAMESPACE = os.getenv("namespace")
        self.BUCKET_NAME = os.getenv("bucket_name")
        self.REGION = os.getenv("region")
        self.object_storage_client = ObjectStorageClient(self.CONFIG)

    def upload_file(self, file_storage, filename):
        try:
            self.object_storage_client.put_object(
                namespace_name=self.NAMESPACE,
                bucket_name=self.BUCKET_NAME,
                object_name=filename,
                put_object_body=file_storage.stream,
                content_type=file_storage.content_type
            )
            return f"https://objectstorage.{self.REGION}.oraclecloud.com/n/{self.NAMESPACE}/b/{self.BUCKET_NAME}/o/{filename}"

        except Exception as e:
            return f"Error uploading to object storage: {e}"

    def get_file_url(self, object_name):
        if not object_name:
            return None
        return f"https://objectstorage.{self.REGION}.oraclecloud.com/n/{self.NAMESPACE}/b/{self.BUCKET_NAME}/o/{object_name}"

    def list_objects(self, prefix=""):
        try:
            response = self.object_storage_client.list_objects(
                namespace_name=self.NAMESPACE,
                bucket_name=self.BUCKET_NAME,
                prefix=prefix
            )
            return response.data.objects
        except Exception as e:
            print(f"Error listing objects: {e}")
            return []