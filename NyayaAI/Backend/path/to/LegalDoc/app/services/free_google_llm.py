import google.generativeai as genai
# from google import genai

from app.config import settings
import logging
import time

logger = logging.getLogger(__name__)

try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    print("Google AI Studio configured successfully")
except Exception as e:
    logger.error(f"Error configuring Google AI: {e}")
    raise

class FreeGoogleLLM:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(settings.LLM_MODEL)
            print(f"Free Gemini model loaded: {settings.LLM_MODEL}")
        except Exception as e:
            logger.error(f"Error loading Gemini model: {e}")
            raise
    
    def generate_legal_explanation(self, prompt: str, max_retries: int = 3) -> str:
        """Generate legal explanation using free Gemini API"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  
                        max_output_tokens=1200,
                        top_p=0.8,
                        top_k=40,
                    )
                )
                return response.text
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  
                        logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "I'm experiencing high demand right now. Please try again in a moment."
                
                logger.error(f"Error with Gemini API (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return f"I apologize, but I'm having trouble processing your request right now. Please try rephrasing your question or try again later."
        
        return "Unable to process request at this time."

try:
    free_google_llm = FreeGoogleLLM()
except Exception as e:
    logger.error(f"Failed to initialize Free Google LLM: {e}")
    free_google_llm = None