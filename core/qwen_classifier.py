"""
FmWk/core/qwen_classifier.py — Lightweight Qwen 4-bit GGUF Tool Classifier
"""

import os
from typing import Dict, Any, List, Optional
import orjson
from FILES.logger import get_logger

logger = get_logger(__name__)

_FMWK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_MODEL_PATH = os.path.join(_FMWK_DIR, "models", "qwen.gguf")


class QwenToolClassifier:
    """
    4-bit Quantized Tool Classifier using llama_cpp.
    Extracts tool targets and parameters from user queries with ~180MB footprint and sub-30ms latency.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or _DEFAULT_MODEL_PATH
        self._llm = None
        self._attempted_load = False

    def _lazy_load(self):
        """Loads Qwen GGUF model once when requested."""
        if self._attempted_load:
            return
        self._attempted_load = True

        if not os.path.isfile(self.model_path):
            logger.info(
                f"Qwen GGUF classifier model not found at {self.model_path}. "
                "Queries will cascade cleanly to ALFRED LLM."
            )
            return

        try:
            from llama_cpp import Llama
            logger.info(f"Loading Qwen 4-bit classifier from {self.model_path}...")
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=512,
                n_threads=2,
                verbose=False
            )
            logger.info("Qwen 4-bit classifier loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load Qwen classifier: {e}")

    def is_ready(self) -> bool:
        """Returns True if the quantized Qwen model is active."""
        self._lazy_load()
        return self._llm is not None

    def classify(self, query: str, available_tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Runs fast inference to map query to tool name and JSON arguments.
        Falls back to None if no tool fits or model is not loaded.
        """
        self._lazy_load()
        if not self._llm or not available_tools:
            return None

        tools_summary = "\n".join(
            f"- {t['name']}: {t.get('description', '')}"
            for t in available_tools
        )

        prompt = (
            f"You are a tool dispatcher. Available tools:\n{tools_summary}\n\n"
            f"Query: \"{query}\"\n"
            "Respond ONLY with valid JSON having 'tool_name' and 'arguments'. "
            "If no tool matches, respond with {}.\n"
            "JSON: "
        )

        try:
            out = self._llm(prompt, max_tokens=100, stop=["\n", "}"], echo=False)
            raw = out["choices"][0]["text"].strip()
            if not raw.endswith("}"):
                raw += "}"
            data = orjson.loads(raw)
            if "tool_name" in data and data["tool_name"]:
                return {
                    "tool_name": data["tool_name"],
                    "arguments": data.get("arguments", {})
                }
        except Exception as e:
            logger.debug(f"Qwen classification parse error: {e}")

        return None
