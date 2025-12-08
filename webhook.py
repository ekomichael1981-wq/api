import logging
import asyncio
from fastapi import FastAPI, Form, Request
from whatsapp_service import whatsapp_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/api/webhook")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    """Handle incoming WhatsApp messages from Twilio."""
    logger.info(f"Received WhatsApp message from {From}: {Body}")
    
    # In a serverless environment like Vercel, background tasks might be cut off 
    # if the response is sent immediately. However, for simple interactions, 
    # we can try to await the handler or use a proper queue in production.
    # For this setup, we'll await it to ensure it runs before the function freezes.
    
    try:
        await whatsapp_service.handle_incoming_message(From, Body)
    except Exception as e:
        logger.error(f"Error handling WhatsApp message: {e}")
        
    return {"status": "received"}

@app.get("/")
async def index():
    return {"status": "Japa Genie WhatsApp Bot is running 🧞‍♂️"}
