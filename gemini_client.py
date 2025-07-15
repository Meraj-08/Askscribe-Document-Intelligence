import os
import logging
from google import genai
from google.genai import types

class GeminiClient:
    """Client for Google Gemini AI integration"""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        
    def generate_answer(self, question: str, context: str) -> str:
        """Generate structured answer based on question and context"""
        try:
            # Create structured prompt for better responses
            system_prompt = """You are AskScribe, an intelligent document analysis assistant. Your task is to provide accurate, structured, and helpful answers based on the provided context from user documents.

RESPONSE GUIDELINES:
1. **Structure**: Use clear headings, bullet points, and numbered lists
2. **Keywords**: Highlight important terms using **bold** formatting
3. **Accuracy**: Only use information from the provided context
4. **Clarity**: Provide point-wise, well-organized answers
5. **Source**: Reference the document context when relevant

If the context doesn't contain sufficient information to answer the question, respond with "**Answer not in context**" followed by a brief explanation.

Format your response in a clear, professional manner suitable for document analysis."""

            user_prompt = f"""**Question**: {question}

**Context from Documents**:
{context}

**Instructions**: Based on the above context, provide a comprehensive, structured answer to the question. Use proper formatting with headings, bullet points, and **bold** keywords where appropriate."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,  # Lower temperature for more focused responses
                    max_output_tokens=2048
                )
            )
            
            if response.text:
                return self._format_response(response.text)
            else:
                return "**Error**: Unable to generate response. Please try again."
                
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return f"**Error**: Failed to generate response - {str(e)}"
    
    def _format_response(self, text: str) -> str:
        """Post-process and format the response"""
        # Ensure proper spacing and formatting
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add extra spacing around headers
                if line.startswith('#') or line.startswith('**') and line.endswith('**'):
                    if formatted_lines and formatted_lines[-1] != '':
                        formatted_lines.append('')
                    formatted_lines.append(line)
                    formatted_lines.append('')
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines).strip()
    
    def summarize_document(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of document content"""
        try:
            prompt = f"""Summarize the following document content in a clear, structured format. Keep the summary under {max_length} words and highlight **key points**.

Document Content:
{text[:4000]}  # Limit input size

Provide a concise summary with bullet points for main topics."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=max_length * 2
                )
            )
            
            return response.text or "Unable to generate summary"
            
        except Exception as e:
            logging.error(f"Document summarization error: {e}")
            return f"Error generating summary: {str(e)}"
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> list:
        """Extract key terms from text"""
        try:
            prompt = f"""Extract the {max_keywords} most important keywords or phrases from the following text. Return only the keywords, one per line, without numbering or bullet points.

Text:
{text[:2000]}"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=200
                )
            )
            
            if response.text:
                keywords = [kw.strip() for kw in response.text.split('\n') if kw.strip()]
                return keywords[:max_keywords]
            
            return []
            
        except Exception as e:
            logging.error(f"Keyword extraction error: {e}")
            return []
