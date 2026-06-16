import os
from openai import AsyncOpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LLMClient:
    def __init__(self, base_url: str = None, api_key: str = None, model_name: str = None):
        self.model_name = model_name or "qwen2.5:7b"
        self.client = AsyncOpenAI(
            base_url=base_url or "http://localhost:11434/v1",
            api_key=api_key or "ollama"
        )

    async def generate_response(self, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7) -> str:
        """
        Generate a text response from the LLM.
        """
        import asyncio
        for attempt in range(4): # Max 4 attempts
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                )
                
                # Handle DashScope non-standard schema where choices might be None
                if getattr(response, "choices", None) and len(response.choices) > 0:
                    return response.choices[0].message.content
                elif getattr(response, "text", None):
                    return response.text
                else:
                    return str(response)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < 3:
                    await asyncio.sleep(2 ** attempt) # Exponential backoff: 1s, 2s, 4s
                    continue
                return f"Error calling LLM: {error_str}"
