import os
from typing import Annotated, Union

from azure.storage.blob import BlobClient, BlobServiceClient
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header


router = APIRouter()
connection_string = os.environ.get('AZ_CONN_STRING')

def create_container(email):
    """
    Creates container in azure blob storage
    :param email:
    :return:
    """
    try:
        service = BlobServiceClient.from_connection_string(conn_str=connection_string)
        service.create_container(email.split("@")[0])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in creating container in azure blob storage --> {e}")

def list_containers():
    """
    Lists containers in azure blob storage
    :return:
    """
    try:
        service = BlobServiceClient.from_connection_string(conn_str=connection_string)
        containers = service.list_containers()
        return containers
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in listing containers in azure blob storage --> {e}")
@router.post("/uploaddoc", tags=["repository"])
async def upload_doc(email_id: Annotated[Union[str, None], Header()],file: UploadFile = File(...)):
    """
    Uploads file to azure blob storage
    :param email_id:
    :param file:
    :return:
    """
    try:
        container = email_id.split("@")[0]
        if container not in [container["name"] for container in list_containers()]:
            create_container(email_id)
        blob = BlobClient.from_connection_string(conn_str=connection_string, container_name=email_id.split("@")[0], blob_name=file.filename)
        blob.upload_blob(file.file.read())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in uploading file to azure blob storage --> {e}")

@router.get("/download_doc", tags=["repository"])
async def download_doc(email_id: Annotated[Union[str, None], Header()], filename: str):
    """
    Downloads file from azure blob storage
    :param email_id:
    :param filename:
    :return:
    """
    try:
        blob_client = BlobClient.from_connection_string(conn_str=connection_string, container_name=email_id.split("@")[0], blob_name=filename)
        with open(filename, "wb") as my_blob:
            blob_data = blob_client.download_blob()
            blob_data.readinto(my_blob)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in downloading file from azure blob storage --> {e}")

@router.get("/preview_doc_url", tags=["repository"])
async def preview_doc(email_id: Annotated[Union[str, None], Header()], filename: str):
    """
    Downloads file from azure blob storage
    :param email_id:
    :param filename:
    :return:
    """
    try:
        blob_client = BlobClient.from_connection_string(conn_str=connection_string, container_name=email_id.split("@")[0], blob_name=filename)
        return blob_client.url
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in downloading file from azure blob storage --> {e}")

@router.get("/list_files", tags=["repository"])
async def list_files(email_id: Annotated[Union[str, None], Header()]):
    """
    Lists files from azure blob storage
    :param email_id:
    :return:
    """
    try:
        service = BlobServiceClient.from_connection_string(conn_str=connection_string)
        container_client = service.get_container_client(str(email_id.split("@")[0]))
        blob_list = container_client.list_blobs()
        return [blob.name for blob in blob_list]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in listing files from azure blob storage --> {e}")

@router.delete("/delete_file", tags=["repository"])
async def delete_file(email_id: Annotated[Union[str, None], Header()], filename: str):
    """
    Deletes file from azure blob storage
    :param email_id:
    :param filename:
    :return:
    """
    try:
        service = BlobServiceClient.from_connection_string(conn_str=connection_string)
        blob_client = service.get_blob_client(container=str(email_id.split("@")[0]), blob=filename)
        blob_client.delete_blob()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in deleting file from azure blob storage --> {e}")


@router.delete("/delete_container", tags=["repository"])
async def delete_container(email_id: Annotated[Union[str, None], Header()]):
    """
    Deletes container from azure blob storage
    :param email_id:
    :return:
    """
    try:
        service = BlobServiceClient.from_connection_string(conn_str=connection_string)
        container_client = service.get_container_client(str(email_id.split("@")[0]))
        container_client.delete_container()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in deleting container from azure blob storage --> {e}")
