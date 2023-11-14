import json
import logging
import os
from typing import Annotated, Union

import certifi
import pymongo
from fastapi import APIRouter, Form, HTTPException, Header

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/write_to_mongo", tags=["mongo_db"])
def write_to_mongo(email_id: Annotated[Union[str, None], Header()], first_name: str = Form(...),
                   last_name: str = Form(...), gender: str = Form(...), age: int = Form(...)) -> str:
    """
    Writes data to mongo db
    :param email_id:
    :param data:
    :return:
    """
    data = {
        "email_id": email_id,
        "First Name": first_name,
        "Last Name": last_name,
        "Age": age,
        "Gender": gender,
    }
    try:
        client = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())
        db = client["insurance_ai"]
        collection = db["user_data"]
        # if email in collection, update else insert
        if email_id in collection.distinct("email_id"):
            collection.update_one({"email_id": email_id}, {"$set": data})
        else:
            collection.insert_one(data)
        logger.info(f"Data written to mongo db")
        return json.dumps({"status": "success"})
    except Exception as e:
        logger.error(f"An Exception Occurred while writing to mongo db --> {e}")
        raise HTTPException(status_code=404, detail=f"Error in writing to mongo db --> {e}")


@router.get("/read_from_mongo", tags=["mongo_db"])
def read_from_mongo(email_id: Annotated[Union[str, None], Header()]) -> str:
    """
    Reads data from mongo db
    :param email_id:
    :return:
    """
    try:
        client = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())
        db = client["mindful_ai"]
        collection = db["user_health_data"]
        data = collection.find_one({"email_id": email_id})
        del data["_id"]
        logger.info(f"Data read from mongo db")
        return json.dumps(data)
    except Exception as e:
        logger.error(f"An Exception Occurred while reading from mongo db --> {e}")
        raise HTTPException(status_code=404, detail=f"Error in reading from mongo db --> {e}")