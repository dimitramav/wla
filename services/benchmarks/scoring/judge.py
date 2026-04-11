"""
Judge LLM builders for the benchmark pipelines.

Two judges are used across the suite:

- Gemini 2.5 Flash Lite — wraps ChatGoogleGenerativeAI inside a RAGAS
  LangchainLLMWrapper subclass that drops RAGAS's per-call `temperature`
  kwarg (langchain-google-genai 1.0.x rejects it; temperature is set at
  init). Used by the LLM benchmark for faithfulness and rubric scoring.

- Ollama (mistral:7b-instruct-q4_0) — wraps ChatOllama for RAGAS
  context_precision scoring during the RAG retrieval benchmark.
"""

import os


def build_gemini_judge():
    """Build Google Gemini 2.5 Flash Lite RAGAS judge wrapper.

    Returns None if `GOOGLE_API_KEY` is not set or setup fails. Callers
    that want a hard failure on missing key should check the return value.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from ragas.llms import LangchainLLMWrapper

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.0,
            max_retries=3,
        )

        class _GeminiJudge(LangchainLLMWrapper):
            def generate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
                result = self.langchain_llm.generate_prompt(
                    prompts=[prompt] * n, stop=stop, callbacks=callbacks,
                )
                if n > 1:
                    result.generations = [[g[0] for g in result.generations]]
                return result

            async def agenerate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
                result = await self.langchain_llm.agenerate_prompt(
                    prompts=[prompt] * n, stop=stop, callbacks=callbacks,
                )
                if n > 1:
                    result.generations = [[g[0] for g in result.generations]]
                return result

        return _GeminiJudge(llm)
    except Exception as e:
        print(f"  ⚠ Gemini judge setup failed: {e}")
        return None


def build_ollama_judge(model: str = "mistral:7b-instruct-q4_0", base_url: str = "http://localhost:11434"):
    """Build a LangChain Ollama wrapper for RAGAS. Returns None on failure."""
    try:
        from langchain_community.chat_models import ChatOllama
        from ragas.llms import LangchainLLMWrapper
        llm = ChatOllama(
            model=model,
            base_url=base_url,
            timeout=300,
        )
        return LangchainLLMWrapper(llm)
    except Exception as e:
        print(f"  [RAGAS LLM setup failed: {e}]")
        return None
