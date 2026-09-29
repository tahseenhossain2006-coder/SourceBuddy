# sourceai/multilingual/translator.py
from typing import Optional
class TranslationProvider:
    async def translate(self, text: str, target: str, source: str = None) -> str:
        raise NotImplementedError

class LLMTranslationProvider(TranslationProvider):
    def __init__(self, llm_service):
        self.llm = llm_service
    async def translate(self, text: str, target: str, source: str = None) -> str:
        prompt = f"Translate the following from {source or 'auto'} to {target}. Return only the translation.\n\n{text}"
        return self.llm.generate_sync(prompt)