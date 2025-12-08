from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os
import random
import asyncio
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

app = FastAPI()

# ========== CONFIGURATION ==========
TELEGRAM_BOT_TOKEN = "8259342334:AAHUXhhi3LcpFv1X5Gt2WN5zRbC9j-VDbNM"
BOT_NAME = "Japa Genie"
VERSION = "2.0"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FEEDBACK SYSTEM (TELEGRAM-CHANNEL BASED) ==========
class FeedbackSystem:
    """Send feedback to your Telegram channel instead of Supabase"""
    
    def __init__(self, bot_token: str, feedback_channel_id: str = None):
        self.bot_token = bot_token
        self.feedback_channel_id = feedback_channel_id or "@JapaGenieFeedback"
        
        # Visa intelligence keywords
        self.visa_keywords = [
            "visa", "immigration", "work permit", "residence permit",
            "green card", "citizenship", "passport", "border control",
            "immigration officer", "visa application", "visa renewal",
            "student visa", "tourist visa", "business visa", "work visa",
            "sponsorship", "documentation", "consulate", "embassy",
            "coe", "certificate of eligibility", "status change",
            "zairyu card", "residence card", "pr", "permanent residence",
            "japan visa", "usa visa", "canada visa", "uk visa", "australia visa",
            "schengen", "immigrant", "migrant", "foreigner", "alien"
        ]
        
        # Store locally as backup
        self.local_storage = "visa_intelligence.jsonl"
    
    def detect_visa_topics(self, text: str) -> List[str]:
        """Detect visa-related keywords in text"""
        text_lower = text.lower()
        detected = []
        
        for keyword in self.visa_keywords:
            if keyword in text_lower:
                # Check context (avoid false positives like "visa credit card")
                if keyword == "visa":
                    if "credit" not in text_lower and "debit" not in text_lower:
                        detected.append(keyword)
                else:
                    detected.append(keyword)
        
        return detected
    
    async def send_to_feedback_channel(self, data: Dict):
        """Send detected conversation to your Telegram channel"""
        try:
            message = f"""
🔔 **VISA INTELLIGENCE ALERT**

👤 User: {data.get('user_name', 'Unknown')}
📝 Keywords: {', '.join(data.get('keywords', []))}
💬 Message: {data.get('text', '')[:200]}...

🏷️ Chat: {data.get('chat_title', 'Private')}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={
                    "chat_id": self.feedback_channel_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
                
                if response.status_code == 200:
                    logger.info(f"✅ Feedback sent to channel: {len(data['keywords'])} keywords")
                else:
                    logger.warning(f"⚠️ Failed to send feedback: {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Feedback channel error: {e}")
    
    def save_locally(self, data: Dict):
        """Save conversation locally as backup"""
        try:
            with open(self.local_storage, "a") as f:
                f.write(json.dumps(data) + "\n")
            logger.info(f"📁 Saved locally: {data.get('user_name')}")
        except Exception as e:
            logger.error(f"❌ Local save error: {e}")

# ========== NATURAL CONVERSATION ENGINE ==========
class ConversationEngine:
    """Make Japa Genie chat naturally in groups"""
    
    def __init__(self):
        self.response_rates = {
            "private": 0.8,
            "group": 0.3,
            "supergroup": 0.25
        }
        
        # Smart response templates
        self.visa_responses = [
            "Interesting visa question! The process can vary quite a bit depending on the country.",
            "That's a common immigration concern. Documentation is usually the key factor.",
            "From what I've seen in the community, that depends on several factors including your background.",
            "Good question! Processing times have been longer than usual lately for many countries.",
            "I've helped others with similar questions. The embassy website usually has the most current info.",
            "That's an important consideration. Many people struggle with that part of the process.",
            "Interesting point! Visa requirements change often, so always check official sources.",
            "From experience, that can be one of the more challenging aspects of immigration."
        ]
        
        self.general_responses = [
            "Thanks for sharing that insight!",
            "That's interesting to know!",
            "Appreciate you bringing that up.",
            "Good point to consider!",
            "Thanks for the perspective!",
            "Interesting discussion!",
            "That's helpful context, thanks!",
            "Appreciate the input!"
        ]
    
    def should_respond(self, message_data: Dict) -> bool:
        """Smart decision engine for responses"""
        text = message_data.get("text", "").strip()
        chat_type = message_data.get("chat_type", "private")
        
        # Don't respond to very short messages
        if len(text.split()) < 3:
            return False
        
        # Don't respond to commands
        if text.startswith("/"):
            return False
        
        # Check if it's a question
        is_question = any(q in text.lower() for q in ['?', 'how', 'what', 'where', 'when', 'why', 'can', 'should', 'does', 'is'])
        
        # Base response rate
        base_rate = self.response_rates.get(chat_type, 0.3)
        
        # Increase rate for questions or visa topics
        if is_question or message_data.get("visa_detected", False):
            base_rate = min(base_rate * 1.5, 0.9)
        
        # Random decision with rate
        return random.random() < base_rate
    
    def generate_response(self, text: str, visa_detected: bool) -> str:
        """Generate natural, helpful response"""
        
        # Choose response category
        if visa_detected:
            responses = self.visa_responses
        else:
            responses = self.general_responses
        
        # Pick random response
        response = random.choice(responses)
        
        # Add human-like variations
        variations = [
            lambda r: r,
            lambda r: r + " :)",
            lambda r: r + "!",
            lambda r: "Hmm... " + r.lower(),
            lambda r: "I see. " + r,
            lambda r: "Interesting. " + r.lower()
        ]
        
        response = random.choice(variations)(response)
        
        # Occasionally add thinking indicator
        if random.random() < 0.2:
            thinkers = ["Let me think... ", "Hmm... ", "That's a good question... "]
            response = random.choice(thinkers) + response
        
        return response
    
    async def simulate_human_delay(self):
        """Simulate human typing/thinking time"""
        delay = random.uniform(1.5, 4.5)
        await asyncio.sleep(delay)

# ========== TELEGRAM BOT CORE ==========
class JapaGenieBot:
    """Main bot functionality"""
    
    def __init__(self):
        self.feedback = FeedbackSystem(TELEGRAM_BOT_TOKEN)
        self.conversation = ConversationEngine()
        self.command_handlers = self._setup_commands()
        
    def _setup_commands(self):
        """Setup command responses"""
        return {
            "/start": self._start_command,
            "/help": self._help_command,
            "/visa": self._visa_command,
            "/work": self._work_command,
            "/study": self._study_command,
            "/countries": self._countries_command,
            "/feedback": self._feedback_command
        }
    
    async def process_message(self, update: Dict) -> Optional[str]:
        """Process incoming Telegram message"""
        try:
            message = update.get("message", {})
            if not message:
                return None
            
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()
            user = message.get("from", {})
            chat_type = message.get("chat", {}).get("type", "private")
            chat_title = message.get("chat", {}).get("title", "Private Chat")
            
            # Skip empty messages
            if not text:
                return None
            
            # ========== VISA INTELLIGENCE DETECTION ==========
            visa_keywords = self.feedback.detect_visa_topics(text)
            visa_detected = len(visa_keywords) > 0
            
            if visa_detected:
                # Prepare feedback data
                feedback_data = {
                    "user_id": user.get("id"),
                    "user_name": user.get("first_name", "Unknown"),
                    "username": user.get("username"),
                    "text": text,
                    "keywords": visa_keywords,
                    "chat_id": chat_id,
                    "chat_title": chat_title,
                    "chat_type": chat_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send to feedback channel
                await self.feedback.send_to_feedback_channel(feedback_data)
                
                # Save locally as backup
                self.feedback.save_locally(feedback_data)
                
                logger.info(f"🎯 Visa detected: {visa_keywords} from {user.get('first_name')}")
            
            # ========== COMMAND HANDLING ==========
            if text.startswith("/"):
                command = text.split()[0].lower()
                if command in self.command_handlers:
                    return await self.command_handlers[command]()
                else:
                    return f"🤔 Unknown command: {command}\nType /help for available commands."
            
            # ========== NATURAL CONVERSATION ==========
            conversation_data = {
                "text": text,
                "chat_type": chat_type,
                "visa_detected": visa_detected
            }
            
            if self.conversation.should_respond(conversation_data):
                # Simulate human delay
                await self.conversation.simulate_human_delay()
                
                # Generate natural response
                response = self.conversation.generate_response(text, visa_detected)
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Process message error: {e}")
            return None
    
    # ========== COMMAND RESPONSES ==========
    async def _start_command(self) -> str:
        return f"""🧞 Welcome to {BOT_NAME} - Your AI Immigration Assistant!

I can help you with:
- Visa requirements & processes
- Work permit information
- Study abroad guidance
- Country-specific immigration tips
- Document checklists

📋 **Available Commands:**
/help - Show all commands
/visa - General visa information
/work - Work permit guides
/study - Study abroad options
/countries - Popular destinations
/feedback - Send feedback

💬 **Or just ask questions like:**
- "Canada PR requirements"
- "UK skilled worker visa"
- "Germany job seeker visa"
- "USA green card process"

I'm here to help 24/7!"""
    
    async def _help_command(self) -> str:
        return """📋 **Japa Genie Commands:**

🧭 **Navigation:**
/start - Welcome message & overview
/help - This help menu

🛂 **Visa Information:**
/visa - General visa types & requirements
/work - Work permit guides for popular countries
/study - Study abroad visa information
/countries - Immigration info by country

📊 **Tools:**
/feedback - Send feedback or report issues

💬 **Just Chat:**
You can also ask natural questions like:
- "How to get Canada PR?"
- "USA H-1B visa process"
- "Germany Blue Card requirements"
- "Australia points calculator"

I'll respond naturally in conversations too!"""
    
    async def _visa_command(self) -> str:
        return """🛂 **Visa Types & Information:**

**Common Visa Categories:**
1. **Tourist Visa** - Short visits, sightseeing
2. **Student Visa** - For education purposes
3. **Work Visa** - Employment opportunities
4. **Business Visa** - Business meetings, conferences
5. **Family Visa** - Joining family members
6. **Permanent Residence** - Long-term settlement

**General Requirements:**
- Valid passport (6+ months validity)
- Completed application forms
- Passport-sized photographs
- Proof of financial means
- Travel itinerary
- Accommodation proof
- Purpose documentation

**Tips:**
- Apply well in advance (1-3 months)
- Check embassy/consulate websites
- Prepare all documents in order
- Consider using immigration lawyers for complex cases"""
    
    async def _work_command(self) -> str:
        return """💼 **Work Visa Comparison:**

🇨🇦 **Canada:**
- Express Entry (FSW, CEC, FST)
- Provincial Nominee Program (PNP)
- Atlantic Immigration Program
- Global Talent Stream
📌 Requirements: Job offer, language test, education assessment

🇺🇸 **USA:**
- H-1B (Specialty occupations)
- L-1 (Intra-company transfer)
- O-1 (Extraordinary ability)
- EB-2/EB-3 (Green Cards)
📌 Requirements: Employer petition, relevant degree/experience

🇬🇧 **UK:**
- Skilled Worker Visa (70+ points)
- Health & Care Worker Visa
- Global Talent Visa
- Scale-up Visa
📌 Requirements: Job offer, English test, minimum salary

🇩�� **Germany:**
- EU Blue Card (University degree + job)
- Job Seeker Visa (6 months)
- Freelancer/Self-employment Visa
📌 Requirements: Recognized degree, job contract

🇦🇺 **Australia:**
- Skilled Independent (189)
- Skilled Nominated (190)
- Employer Sponsored (482, 186)
📌 Requirements: Occupation list, points test, skills assessment"""
    
    async def _study_command(self) -> str:
        return """🎓 **Study Abroad Guide:**

**Top Destinations:**
🇺🇸 **USA:**
- F-1 Student Visa
- OPT (Optional Practical Training) - 1-3 years
- Ivy League & state universities
- High tuition, excellent opportunities

🇨🇦 **Canada:**
- Study Permit
- PGWP (Post-Graduation Work Permit) - up to 3 years
- Affordable tuition, PR pathways
- Co-op programs available

🇬🇧 **UK:**
- Student Visa
- Graduate Route - 2-3 years work
- Russell Group universities
- Shorter programs (1-year masters)

🇩🇪 **Germany:**
- Student Visa
- 18-month job seeker after graduation
- FREE tuition at public universities
- Strong engineering/tech programs

🇦🇺 **Australia:**
- Student Visa
- Temporary Graduate Visa (2-4 years)
- Work during studies (40 hrs/fortnight)
- Strong research universities

**Requirements:**
- University acceptance letter
- Proof of funds
- Language proficiency (IELTS/TOEFL)
- Medical insurance
- Genuine Temporary Entrant statement"""
    
    async def _countries_command(self) -> str:
        return """🌍 **Popular Immigration Destinations:**

🇨🇦 **Canada:**
- Express Entry points system
- Provincial nominations available
- Family sponsorship options
- Processing: 6-8 months
- Language: English/French required

🇺🇸 **USA:**
- Employment-based preference system
- H-1B lottery annually
- Family-based categories
- Processing: 1-3 years
- PERM labor certification needed

🇬🇧 **UK:**
- Points-based immigration system
- Minimum salary thresholds
- Health surcharge required
- Processing: 3-6 months
- English language requirement

🇩🇪 **Germany:**
- EU Blue Card fastest route
- Recognition of foreign degrees
- Permanent residence in 21-33 months
- Processing: 1-3 months
- German language beneficial

🇦🇺 **Australia:**
- SkillSelect points test
- Occupation lists (MLTSSL/STSOL)
- Regional visas available
- Processing: 8-12 months
- Points minimum: 65

🇯🇵 **Japan:**
- Engineer/Specialist in Humanities
- Highly Skilled Professional (point system)
- Student to work transition common
- Processing: 1-2 months
- Japanese language helpful

**Ask about specific countries for more details!**"""
    
    async def _feedback_command(self) -> str:
        return """📣 **Feedback & Suggestions:**

Thank you for using Japa Genie! Your feedback helps me improve.

**How to provide feedback:**
1. Just chat with me naturally - I learn from conversations
2. Report issues directly in chat
3. Suggest new features or information

**What I'm tracking (anonymously):**
- Common visa questions asked
- Areas where people need more clarity
- Country-specific information gaps
- Response effectiveness

**Privacy Note:**
I only collect conversation content related to immigration topics to improve my knowledge base. No personal identifiable information is stored.

**Contact:**
For urgent matters, please use the /start command to see contact options.

Thank you for helping me become a better immigration assistant! 🧞"""

# Initialize bot
bot = JapaGenieBot()

# ========== FASTAPI ENDPOINTS ==========
@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint"""
    try:
        update = await request.json()
        logger.info(f"📨 Received update: {update.get('update_id')}")
        
        response_text = await bot.process_message(update)
        
        if response_text:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            
            # Send typing action
            await send_typing_action(chat_id)
            
            # Small delay before sending
            await asyncio.sleep(0.5)
            
            # Send response
            await send_telegram_message(chat_id, response_text)
        
        return JSONResponse({"ok": True})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse({"ok": True})

@app.get("/")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "japa-genie-bot",
        "version": VERSION,
        "bot_name": BOT_NAME,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    """Get bot statistics"""
    try:
        with open("visa_intelligence.jsonl", "r") as f:
            lines = f.readlines()
        
        return {
            "status": "online",
            "visa_conversations_logged": len(lines),
            "last_updated": datetime.now().isoformat(),
            "bot": BOT_NAME,
            "version": VERSION
        }
    except:
        return {
            "status": "online",
            "visa_conversations_logged": 0,
            "bot": BOT_NAME,
            "version": VERSION
        }

# ========== TELEGRAM API HELPERS ==========
async def send_telegram_message(chat_id: int, text: str):
    """Send message via Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            })
    except Exception as e:
        logger.error(f"❌ Send message error: {e}")

async def send_typing_action(chat_id: int):
    """Send typing indicator"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "action": "typing"
            })
    except:
        pass

async def set_webhook(webhook_url: str):
    """Set Telegram webhook"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"url": webhook_url})
            return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info(f"🚀 {BOT_NAME} v{VERSION} starting up...")
    logger.info("✅ Bot initialized and ready")^X
mv bot.py.save bot.py
ls -la
wc -l bot.py

