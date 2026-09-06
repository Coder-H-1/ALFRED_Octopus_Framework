"""
FmWk/core/qwen_classifier.py — Warm Resident LLM Tool Classifier for Natural Voice Queries
"""

import os
from typing import Dict, Any, List, Optional
import orjson
from FILES.logger import get_logger

logger = get_logger(__name__)

_FMWK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_MODEL_PATH = os.path.join(_FMWK_DIR, "models", "qwen.gguf")


def _extract_first_json(text: str) -> Optional[dict]:
    """Extracts first valid balanced JSON object from model output with auto-closing fallback."""
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return orjson.loads(text[start:i+1])
                except Exception:
                    return None
    # If unclosed at max_tokens limit, try auto-closing
    try:
        candidate = text[start:].strip()
        if not candidate.endswith("}"):
            candidate += "}"
        return orjson.loads(candidate)
    except Exception:
        pass
    return None


class QwenToolClassifier:
    """
    Resident, warm LLM tool classifier.
    Loads once at startup without retirement to eliminate cold-start latency.
    Maps variable natural language speech into structured tool calls and arguments.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or _DEFAULT_MODEL_PATH
        self._llm = None
        self._warm = False
        self.warmup()

    def warmup(self):
        """Eagerly loads and warms up the LLM instance at startup."""
        if self._warm:
            return

        # 1. Dedicated fast classifier GGUF if available
        if os.path.isfile(self.model_path):
            try:
                from llama_cpp import Llama
                logger.info(f"Loading warm dedicated classifier from {self.model_path}...")
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=512,
                    n_threads=4,
                    verbose=False
                )
                self._warm = True
                logger.info("Dedicated warm tool classifier online.")
                return
            except Exception as e:
                logger.warning(f"Failed to load dedicated classifier: {e}")

        # 2. Fallback to ALFRED's warm resident LLM instance
        try:
            from FILES.utils import LLM
            self._llm = LLM
            self._warm = True
            logger.info("Hooked into ALFRED warm resident LLM instance for tool classification.")
        except Exception as e:
            logger.warning(f"Could not hook into ALFRED LLM: {e}")

    def is_ready(self) -> bool:
        """Returns True if warm classifier is loaded."""
        if not self._warm:
            self.warmup()
        return self._llm is not None

    def classify(self, query: str, available_tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Runs flexible intent classification on user query against available tools.
        Handles natural speech variations (variable keywords) into structured tool calls.
        Returns {'tool_name': str, 'arguments': dict} or None.
        """
        if not self.is_ready() or not available_tools:
            return None

        tools_summary = "\n".join(
            f"- {t['name']}: {t.get('description', '')}"
            for t in available_tools
        )

        prompt = (
            "You are ALFRED's tool dispatcher. Match the user's intent to the most appropriate tool.\n"
            "If user command matches a tool, extract its arguments and output strictly JSON.\n"
            "If general chitchat or no tool applies, output {}\n\n"
            f"Available tools:\n{tools_summary}\n\n"
            "Examples of variable intent matching:\n"
            "User command: \"it's way too loud here\"\n"
            "JSON: {\"tool_name\": \"system_adjust_volume\", \"arguments\": {\"direction\": \"decrease\"}}\n\n"
            "User command: \"dim the display a bit\"\n"
            "JSON: {\"tool_name\": \"adjust_screen_brightness\", \"arguments\": {\"direction\": \"decrease\"}}\n\n"
            "User command: \"can you put on some coldplay\"\n"
            "JSON: {\"tool_name\": \"youtube_play\", \"arguments\": {\"query\": \"coldplay\"}}\n\n"
            "User command: \"who invented the lightbulb\"\n"
            "JSON: {\"tool_name\": \"web_search_extract\", \"arguments\": {\"query\": \"who invented the lightbulb\"}}\n\n"
            "User command: \"how much battery is left\"\n"
            "JSON: {\"tool_name\": \"get_battery_status\", \"arguments\": {}}\n\n"
            f"User command: \"{query}\"\n"
            "JSON: "
        )

        try:
            out = self._llm(
                prompt,
                max_tokens=60,
                stop=["\n\n", "User:", "ALFRED:", "\nUser command:", "}\n"],
                echo=False,
                temperature=0.1
            )
            raw = out["choices"][0]["text"].strip()
            data = _extract_first_json(raw)
            if data and "tool_name" in data and data["tool_name"]:
                predicted_tool = str(data["tool_name"]).strip()
                valid_names = {t["name"] for t in available_tools}
                if predicted_tool in valid_names:
                    return {
                        "tool_name": predicted_tool,
                        "arguments": data.get("arguments", {})
                    }
                else:
                    logger.debug(f"Classifier suggested non-existent tool: {predicted_tool}")
        except Exception as e:
            logger.debug(f"Tool classification inference error: {e}")

        return None
