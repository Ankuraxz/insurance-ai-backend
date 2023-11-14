import os
from typing import Annotated, Union

import certifi
import pymongo
from fastapi import APIRouter, Form, HTTPException, Header
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Milvus

from settings.config import Config

openai_llm_chat = Config.get_openai_chat_connection
router = APIRouter()

client = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())


def read_from_embeddings(email: str, query: str) -> str:
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = Milvus(embeddings, collection_name=email.split('@')[0], connection_args={
            "host": "20.106.234.205",
            "port": "19530",

        })

        qa = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=vectorstore.as_retriever())
        docs = qa({"query": query})
        return docs["result"]


    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in reading from milvius --> {e}")


def read_from_mongo(email: str) -> str:
    try:
        client_mongo = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())
        db = client["insurance_ai"]
        collection = db["user_data"]
        data = collection.find_one({"email_id": email})
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in reading from mongo db --> {e}")


@router.post("/chat", tags=["ai"])
async def chat(email_id: Annotated[Union[str, None], Header()], message: str = Form(...), history: list = Form(...),
               document_type: str = Form(...)):
    """
    Chat with the AI to know about personality
    :header: user_email
    :param: message
    :param: history
    :return: message, reply
    """

    if history is None:
        history = []

    if "STOP" in message or "Stop" in message or "stop" in message:
        return {"response": "STOPPING CHAT ", "history": history, "stop": True}

    inference = read_from_embeddings(email_id, message)

    template = """
    CONTEXT: You are an AI Agent, and you are chatting with a customer who wants to know more 
    about their {document_type}. A user with name {name} will be chatting with you 
    to know more about their document, and may ask related questions. Politely answer them. Here is the history of 
    chat {history}, now the customer is saying {message}. In case there is no history of chat, just respond to the 
    customer's current message. 

    DATA FROM DOCUMENTS: {inference} is the data relevant to message Query fetched from  Documents uploaded by the user,  Your answers should be strictly based on it. 

    ANSWER: Keep Answers short and simple, preferable in bullets.

    RESPONSE CONSTRAINT: DO NOT OUTPUT HISTORY OF CHAT, JUST OUTPUT RESPONSE TO THE CUSTOMER IN BULLET POINTS.
    """

    prompt = PromptTemplate.from_template(template)
    chain = prompt | openai_llm_chat

    response = chain.invoke(
        {"inference": inference, "message": message, "history": history, "name": email_id.split("@")[0],
         "document_type": document_type})

    if "STOP" in response or "Stop" in response or "stop" in response or "STOPPING CHAT" in response or "Stopping Chat" in response or "stopping chat" in response:
        return {"response": response, "history": history, "stop": True}
    else:
        history.append({"message": message, "response": response})
        return {"response": response, "history": history, "stop": False}


@router.post("/savechat", tags=["ai"])
def savechat(email_id: Annotated[Union[str, None], Header()], history: list = Form(...), document_type: str = Form(...) ):
    """
    Save chat to mongo db
    :header: user_email
    :param: history
    :return: message
    """
    try:
        client_mongo = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())
        db = client["insurance_ai"]
        collection = db["chat_data"]
        data = collection.find_one({"email_id": email_id})
        if data is None:
            collection.insert_one({"email_id": email_id, "history": history, "document_type": document_type})
        else:
            collection.update_one({"email_id": email_id}, {"$set": {"history": history, "document_type": document_type}})
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in writing to mongo db --> {e}")


@router.get("/retrivechat", tags=["ai"])
def retrivechat(email_id: Annotated[Union[str, None], Header()], document_type: str = Form(...)):
    """
    Read chat from mongo db
    :header: user_email
    :param: doc type
    :return: message
    """
    try:
        client_mongo = pymongo.MongoClient(os.environ.get('MONGO_URI'), ssl=True, tlsCAFile=certifi.where())
        db = client["insurance_ai"]
        collection = db["chat_data"]
        data = collection.find_one({"email_id": email_id, "document_type": document_type})
        if data is None:
            return {"message": "No chat found"}
        else:
            del data["_id"]
            return {"message": data["history"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error in reading from mongo db --> {e}")


