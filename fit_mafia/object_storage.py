import os
import oci
from oci.object_storage import ObjectStorageClient

class ObjectStorageManager:
    def __init__(self):
        self.config = oci.config.from_file(file_location=os.getenv("config"), profile_name="DEFAULT")
        self.namespace = os.getenv("namespace")
        self.bucket_name = os.getenv("bucket_name")
        self.region = os.getenv("region")
        self.object_storage_client = ObjectStorageClient(self.config)

    def upload_file(self, file_storage, filename):
        try:
            self.object_storage_client.put_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=filename,
                put_object_body=file_storage.stream,
                content_type=file_storage.content_type
            )
            return "Upload successful."
        except Exception as e:
            return f"Error uploading to object storage: {e}"

    def get_file_url(self, object_name):
        if not object_name:
            return None
        return f"https://objectstorage.{self.region}.oraclecloud.com/n/{self.namespace}/b/{self.bucket_name}/o/{object_name}"

    def list_objects(self, prefix=""):
        try:
            response = self.object_storage_client.list_objects(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                prefix=prefix
            )
            return response.data.objects
        except Exception as e:
            print(f"Error listing objects: {e}")
            return []