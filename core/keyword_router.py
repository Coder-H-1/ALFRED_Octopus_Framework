"""
FmWk/core/keyword_router.py — Strategy B Fast-Path Intent & Keyword Matcher
"""

import re
from typing import Dict, Any, Optional, Tuple, List

class KeywordRouter:
    """
    Sub-1ms keyword and regex rule matcher.
    Extracts tool targets and basic arguments from natural voice/text commands.
    """

    def __init__(self):
        # List of rules: (compiled_regex, tool_name, argument_extractor_fn)
        self._rules: List[Tuple[re.Pattern, str, Any]] = []
        self._init_default_rules()

    def _init_default_rules(self):
        # 1. Volume Control: "set volume to 50", "volume 80", "mute volume"
        def extract_volume(m: re.Match) -> Dict[str, Any]:
            val = m.group(1)
            if val.lower() == "mute":
                return {"level": 0}
            return {"level": int(val)}

        self.register_rule(
            r"(?:set\s+)?volume\s+(?:to\s+)?(mute|\d+)",
            "system_set_volume",
            extract_volume
        )

        # 2. Web Search: "search for python tutorials", "google weather today", "look up recipes"
        def extract_search(m: re.Match) -> Dict[str, Any]:
            return {"query": m.group(1).strip()}

        self.register_rule(
            r"(?:search(?:\s+for|\s+web)?|google|look\s+up)\s+(.+)",
            "web_search",
            extract_search
        )

        # 3. Application Launcher: "open notepad", "launch calculator", "start browser"
        def extract_app(m: re.Match) -> Dict[str, Any]:
            return {"app_name": m.group(1).strip()}

        self.register_rule(
            r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)",
            "app_open",
            extract_app
        )

        # 4. Battery Status: "battery status", "battery level", "how much battery"
        self.register_rule(
            r"(?:check\s+)?battery(?:\s+status|\s+level|\s+percentage)?|how\s+much\s+battery",
            "get_battery_status",
            lambda m: {}
        )

        # 5. Screen Brightness: "set brightness to 70", "brightness 50"
        self.register_rule(
            r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)",
            "set_screen_brightness",
            lambda m: {"level": int(m.group(1))}
        )

        # 6. Current Brightness: "check brightness", "what is screen brightness"
        self.register_rule(
            r"(?:check|get|what\s+is\s+(?:the\s+)?|current\s+)?(?:screen\s+)?brightness",
            "get_screen_brightness",
            lambda m: {}
        )

        # 7. Media Controls: "pause music", "resume media", "next song", "stop music"
        self.register_rule(
            r"(?:pause|resume|toggle\s+media|play\s+media|pause\s+media|pause\s+music|resume\s+music)",
            "media_play_pause",
            lambda m: {}
        )
        self.register_rule(
            r"(?:next\s+song|next\s+track|skip\s+song|skip\s+track)",
            "media_next",
            lambda m: {}
        )
        self.register_rule(
            r"(?:previous\s+song|previous\s+track|last\s+song)",
            "media_previous",
            lambda m: {}
        )
        self.register_rule(
            r"(?:stop\s+media|stop\s+music)",
            "media_stop",
            lambda m: {}
        )

    def register_rule(self, pattern: str, tool_name: str, extractor_fn):
        """Registers a new fast-path regex rule."""
        compiled = re.compile(pattern, re.IGNORECASE)
        self._rules.append((compiled, tool_name, extractor_fn))

    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Tests the text against fast rules.
        Returns tool name and extracted arguments if matched, else None.
        """
        clean_text = text.strip()
        for pattern, tool_name, extractor in self._rules:
            m = pattern.search(clean_text)
            if m:
                try:
                    args = extractor(m)
                    return {
                        "matched": True,
                        "tool_name": tool_name,
                        "arguments": args,
                        "strategy": "keyword_fast_path"
                    }
                except Exception:
                    continue
        return None
