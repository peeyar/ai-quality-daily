"""Gemini 2.5 Pro judge for DeepEval GEval scoring.

Mirrors the pattern from careertailer/backend/tests/deepeval_setup.py.
The judge is intentionally a different model than the agent's runtime LLM
(gemini-2.5-flash). Using gemini-2.5-pro for the judge keeps "what we score"
and "what we judge" structurally separated.
"""
import os
from typing import Any

from deepeval.models.base_model import DeepEvalBaseLLM
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class GeminiJudge(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "gemini-2.5-pro", temperature: float = 0.0):
        self._model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.environ["GEMINI_API_KEY"],
        )
        self._model_name = model_name

    def load_model(self) -> Any:
        return self._model

    def generate(self, prompt: str) -> str:
        return self._model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        result = await self._model.ainvoke(prompt)
        return result.content

    def get_model_name(self) -> str:
        return self._model_name


def get_judge() -> GeminiJudge:
    """Singleton-style accessor."""
    return GeminiJudge()
