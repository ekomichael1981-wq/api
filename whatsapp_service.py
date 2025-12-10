import os
import logging
import asyncio
from twilio.rest import Client
from orchestrator_client import orchestrator_client

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886") # Default sandbox

WELCOME_MESSAGE = """Welcome to Japa Genie v2 🧞‍♂️✨
The only japa bot wey dey talk Pidgin, draw your exact path, and send voice note like your sharp uncle.
Just type your age, degree, work exp, IELTS, money, marital status…
Example: 28, B.Sc Comp Sci, 3 yrs dev, IELTS 7.5, ₦8m, single"""

FALLBACK_MESSAGE = "Genie dey rest small… I go ping you when e wake. No wahala, your japa still dey queue 🧞‍♂️"

class WhatsAppService:
    def __init__(self):
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        else:
            self.client = None
            logger.warning("Twilio credentials not set. WhatsApp service will not work.")

    async def send_multimodal_response(self, to_number: str, result: dict):
        """Sends Text -> Image -> Voice in order via Twilio."""
        if not self.client:
            return

        try:
            # 1. Text
            if "text_response" in result:
                self.client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=to_number,
                    body=result["text_response"]
                )
            
            # 2. Image
            if "image_url" in result and result["image_url"]:
                self.client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=to_number,
                    media_url=[result["image_url"]]
                )

            # 3. Voice
            if "voice_url" in result and result["voice_url"]:
                self.client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=to_number,
                    media_url=[result["voice_url"]]
                )
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp response: {e}")

    async def handle_incoming_message(self, from_number: str, body: str):
        """Handles incoming WhatsApp message."""
        if not self.client:
            return

        # Check for start command or first time (simplified)
        if body.lower().strip() == "/start":
             self.client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number,
                body=WELCOME_MESSAGE
            )
             return

        try:
            # Call Orchestrator
            result = await orchestrator_client.query_orchestrator(body)
            await self.send_multimodal_response(from_number, result)

        except TimeoutError:
            # Send Fallback Message
            self.client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number,
                body=FALLBACK_MESSAGE
            )
            
            # Define callback for retry loop
            async def retry_callback(result):
                await self.send_multimodal_response(from_number, result)

            # Start background retry loop
            # NOTE: In serverless (Vercel), this background task will likely fail/stop when the function returns.
            asyncio.create_task(orchestrator_client.retry_loop(body, retry_callback))

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")
            self.client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number,
                body="Wahala dey o. Try again later."
            )

whatsapp_service = WhatsAppService()
