"""
AI service for generating email replies using various AI providers
"""

import asyncio
import httpx
from typing import Optional, Dict, Any
import logging
import json
import google.generativeai as genai
from openai import AsyncOpenAI

from core.config import settings, AI_PROVIDERS, EMAIL_TEMPLATES
from core.logger import email_logger

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered email reply generation"""
    
    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients"""
        try:
            # Initialize Gemini
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini AI client initialized")
            
            # Initialize OpenAI
            if settings.OPENAI_API_KEY:
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
                
        except Exception as e:
            logger.error(f"Error initializing AI clients: {e}")
    
    async def generate_reply(self, 
                           subject: str, 
                           body: str, 
                           sender: str = "",
                           context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate AI reply based on email content"""
        
        provider = settings.AI_PROVIDER.lower()
        
        try:
            if provider == "gemini" and self.gemini_client:
                return await self._generate_gemini_reply(subject, body, sender, context)
            elif provider == "openai" and self.openai_client:
                return await self._generate_openai_reply(subject, body, sender, context)
            else:
                logger.warning(f"AI provider '{provider}' not available, using template")
                return self._get_template_reply(subject, body, sender)
                
        except Exception as e:
            logger.error(f"Error generating AI reply: {e}")
            return self._get_template_reply(subject, body, sender)
    
    async def _generate_gemini_reply(self, 
                                   subject: str, 
                                   body: str, 
                                   sender: str,
                                   context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate reply using Gemini AI"""
        try:
            prompt = self._build_prompt(subject, body, sender, context)
            
            response = await asyncio.to_thread(
                self.gemini_client.generate_content,
                prompt
            )
            
            if response and response.text:
                reply = response.text.strip()
                
                # Clean up the reply
                reply = self._clean_ai_response(reply)
                
                email_logger.log_email_replied(sender, subject, "ai_gemini")
                return reply
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating Gemini reply: {e}")
            return None
    
    async def _generate_openai_reply(self, 
                                   subject: str, 
                                   body: str, 
                                   sender: str,
                                   context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate reply using OpenAI"""
        try:
            prompt = self._build_prompt(subject, body, sender, context)
            
            response = await self.openai_client.chat.completions.create(
                model=AI_PROVIDERS["openai"]["model"],
                messages=[
                    {"role": "system", "content": "You are a professional email assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=AI_PROVIDERS["openai"]["max_tokens"],
                temperature=AI_PROVIDERS["openai"]["temperature"]
            )
            
            if response.choices and response.choices[0].message:
                reply = response.choices[0].message.content.strip()
                
                # Clean up the reply
                reply = self._clean_ai_response(reply)
                
                email_logger.log_email_replied(sender, subject, "ai_openai")
                return reply
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating OpenAI reply: {e}")
            return None
    
    def _build_prompt(self, 
                     subject: str, 
                     body: str, 
                     sender: str,
                     context: Optional[Dict[str, Any]] = None) -> str:
        """Build AI prompt for email reply generation"""
        
        context = context or {}
        company_name = context.get('company_name', settings.FROM_NAME)
        
        prompt = f"""
        You are an AI assistant helping to generate professional email replies for {company_name}.
        
        GUIDELINES:
        - Be professional, helpful, and concise
        - Address the sender's concerns directly
        - Use a friendly but professional tone
        - Keep the response under 200 words
        - Do not include any HTML tags or special formatting
        - End with an appropriate professional closing
        
        EMAIL TO RESPOND TO:
        From: {sender}
        Subject: {subject}
        
        Body:
        {body}
        
        CONTEXT:
        {json.dumps(context, indent=2) if context else "No additional context provided."}
        
        Please generate a professional email reply that addresses the sender's message appropriately.
        Do not include "AI Generated Reply:" or any similar prefixes in your response.
        """
        
        return prompt.strip()
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean and format AI response"""
        # Remove common AI response indicators
        prefixes_to_remove = [
            "AI Generated Reply:",
            "Reply:",
            "Response:",
            "Dear Sir/Madam",
            "Dear Customer"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Remove excessive whitespace
        response = '\n'.join(line.strip() for line in response.split('\n') if line.strip())
        
        # Ensure proper greeting if not present
        if not any(greeting in response.lower()[:50] for greeting in ['dear', 'hello', 'hi', 'thank you']):
            response = f"Dear {settings.FROM_NAME} User,\n\n{response}"
        
        # Ensure proper closing if not present
        closing_phrases = ['best regards', 'sincerely', 'thank you', 'regards']
        if not any(phrase in response.lower()[-100:] for phrase in closing_phrases):
            response += f"\n\nBest regards,\n{settings.FROM_NAME} Team"
        
        return response
    
    def _get_template_reply(self, subject: str, body: str, sender: str) -> str:
        """Get template-based reply as fallback"""
        
        # Determine template type based on subject/body content
        content_lower = f"{subject} {body}".lower()
        
        if any(word in content_lower for word in ['support', 'help', 'issue', 'problem']):
            template_key = "support_auto_reply"
        elif any(word in content_lower for word in ['sales', 'price', 'quote', 'purchase']):
            template_key = "sales_auto_reply"
        else:
            template_key = "default_auto_reply"
        
        template = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["default_auto_reply"])
        
        # Format template with available variables
        return template.format(
            sender_name=settings.FROM_NAME,
            ticket_id=f"TK-{hash(subject + sender) % 100000:05d}"
        )
    
    async def analyze_email_sentiment(self, body: str) -> Dict[str, Any]:
        """Analyze email sentiment using AI"""
        try:
            if settings.AI_PROVIDER == "gemini" and self.gemini_client:
                prompt = f"""
                Analyze the sentiment and urgency of this email:
                
                {body}
                
                Return a JSON response with:
                - sentiment: positive, negative, or neutral
                - urgency: low, medium, or high
                - confidence: 0.0 to 1.0
                - keywords: list of important keywords
                """
                
                response = await asyncio.to_thread(
                    self.gemini_client.generate_content,
                    prompt
                )
                
                if response and response.text:
                    try:
                        # Try to parse JSON response
                        analysis = json.loads(response.text.strip())
                        return analysis
                    except json.JSONDecodeError:
                        # Fallback to basic analysis
                        return self._basic_sentiment_analysis(body)
            
            return self._basic_sentiment_analysis(body)
            
        except Exception as e:
            logger.error(f"Error analyzing email sentiment: {e}")
            return self._basic_sentiment_analysis(body)
    
    def _basic_sentiment_analysis(self, body: str) -> Dict[str, Any]:
        """Basic sentiment analysis without AI"""
        body_lower = body.lower()
        
        # Positive indicators
        positive_words = ['thank', 'great', 'excellent', 'love', 'appreciate', 'good']
        positive_count = sum(1 for word in positive_words if word in body_lower)
        
        # Negative indicators
        negative_words = ['problem', 'issue', 'error', 'bug', 'complaint', 'wrong', 'bad']
        negative_count = sum(1 for word in negative_words if word in body_lower)
        
        # Urgency indicators
        urgent_words = ['urgent', 'asap', 'immediately', 'emergency', 'critical']
        urgent_count = sum(1 for word in urgent_words if word in body_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Determine urgency
        if urgent_count > 0 or len(body) > 500:
            urgency = "high"
        elif negative_count > 1:
            urgency = "medium"
        else:
            urgency = "low"
        
        return {
            "sentiment": sentiment,
            "urgency": urgency,
            "confidence": 0.6,  # Basic analysis confidence
            "keywords": list(set([word for word in positive_words + negative_words + urgent_words if word in body_lower]))
        }
    
    async def suggest_reply_type(self, 
                               subject: str, 
                               body: str, 
                               sender: str) -> Dict[str, Any]:
        """Suggest the best reply type for the email"""
        
        analysis = await self.analyze_email_sentiment(body)
        
        # Determine suggested reply type
        if analysis.get("urgency") == "high":
            reply_type = "immediate"
        elif analysis.get("sentiment") == "negative":
            reply_type = "support"
        elif "sales" in f"{subject} {body}".lower():
            reply_type = "sales"
        else:
            reply_type = "standard"
        
        return {
            "suggested_type": reply_type,
            "confidence": analysis.get("confidence", 0.5),
            "reasoning": f"Based on {analysis.get('sentiment')} sentiment and {analysis.get('urgency')} urgency",
            "analysis": analysis
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of AI service"""
        try:
            status = {
                "status": "healthy",
                "providers": {}
            }
            
            # Test Gemini
            if settings.GEMINI_API_KEY and self.gemini_client:
                try:
                    test_response = await asyncio.to_thread(
                        self.gemini_client.generate_content,
                        "Test message - please respond with 'OK'"
                    )
                    
                    status["providers"]["gemini"] = {
                        "available": True,
                        "response_received": bool(test_response and test_response.text)
                    }
                except Exception as e:
                    status["providers"]["gemini"] = {
                        "available": False,
                        "error": str(e)
                    }
            
            # Test OpenAI
            if settings.OPENAI_API_KEY and self.openai_client:
                try:
                    test_response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Test message - please respond with 'OK'"}],
                        max_tokens=10
                    )
                    
                    status["providers"]["openai"] = {
                        "available": True,
                        "response_received": bool(test_response.choices)
                    }
                except Exception as e:
                    status["providers"]["openai"] = {
                        "available": False,
                        "error": str(e)
                    }
            
            # Check if any provider is available
            if not any(provider.get("available", False) for provider in status["providers"].values()):
                status["status"] = "unhealthy"
                status["error"] = "No AI providers available"
            
            return status
            
        except Exception as e:
            logger.error(f"Error in AI service health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Create AI service instance
ai_service = AIService()
