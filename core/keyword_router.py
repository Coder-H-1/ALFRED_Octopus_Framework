"""
FmWk/core/keyword_router.py — Strategy B Fast-Path Intent & Keyword Matcher
"""

import re
from typing import Dict, Any, Optional, Tuple, List

class KeywordRouter:
    """
    Sub-1ms keyword and regex rule matcher.
    Extracts tool targets and basic arguments from obvious voice/text commands.
    """

    def __init__(self):
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

        def extract_volume_adjust(m: re.Match) -> Dict[str, Any]:
            text = m.group(0).lower()
            direction = "increase" if any(w in text for w in ["up", "louder", "raise", "increase"]) else "decrease"
            return {"direction": direction}

        self.register_rule(
            r"(?:volume\s+(?:up|down)|turn\s+(?:the\s+)?volume\s+(?:up|down)|(?:increase|decrease|raise|lower)\s+(?:the\s+)?volume|louder|quieter)",
            "system_adjust_volume",
            extract_volume_adjust
        )

        self.register_rule(
            r"(?:mute\s+(?:audio|volume|sound)|unmute\s+(?:audio|volume|sound)|^mute$|^unmute$)",
            "system_mute_volume",
            lambda m: {}
        )

        # 2. YouTube Playback
        def extract_youtube(m: re.Match) -> Dict[str, Any]:
            q = m.group(1) or (m.group(2) if m.lastindex >= 2 else None) or (m.group(3) if m.lastindex >= 3 else "")
            return {"query": str(q).strip()}

        self.register_rule(
            r"(?:play\s+(.+?)\s+(?:on|from)\s+youtube|play\s+youtube\s+(.+)|on\s+youtube\s+play\s+(.+))",
            "youtube_play",
            extract_youtube
        )

        self.register_rule(
            r"(?:stop\s+youtube|close\s+youtube|end\s+youtube|stop\s+music)",
            "youtube_stop",
            lambda m: {}
        )

        self.register_rule(
            r"(?:set\s+)?youtube\s+volume\s+(?:to\s+)?(\d+)",
            "youtube_set_volume",
            lambda m: {"level": int(m.group(1))}
        )

        # 3. Web Search & Wikipedia Extraction
        def extract_search(m: re.Match) -> Dict[str, Any]:
            return {"query": m.group(1).strip()}

        self.register_rule(
            r"(?:search(?:\s+for|\s+web)?|google|look\s+up|who\s+is|what\s+is|tell\s+me\s+about)\s+(.+)",
            "web_search_extract",
            extract_search
        )

        # 4. Application Launcher
        def extract_app(m: re.Match) -> Dict[str, Any]:
            return {"app_name": m.group(1).strip()}

        self.register_rule(
            r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)",
            "app_open",
            extract_app
        )

        # 5. Resource Monitoring
        self.register_rule(
            r"(?:check\s+)?(?:system\s+status|system\s+health|resource\s+status)",
            "get_resource_summary",
            lambda m: {}
        )
        self.register_rule(
            r"(?:check\s+)?(?:cpu\s+usage|ram\s+usage|memory\s+usage)",
            "get_system_resources",
            lambda m: {}
        )
        self.register_rule(
            r"(?:check\s+)?process\s+(?:memory|usage|resources)",
            "get_process_resources",
            lambda m: {}
        )

        # 6. Battery & Brightness
        self.register_rule(
            r"(?:check\s+)?battery(?:\s+status|\s+level|\s+percentage)?|how\s+much\s+battery",
            "get_battery_status",
            lambda m: {}
        )
        self.register_rule(
            r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)",
            "set_screen_brightness",
            lambda m: {"level": int(m.group(1))}
        )

        def extract_brightness_adjust(m: re.Match) -> Dict[str, Any]:
            text = m.group(0).lower()
            direction = "increase" if any(w in text for w in ["up", "raise", "increase", "bright"]) else "decrease"
            return {"direction": direction}

        self.register_rule(
            r"(?:brightness\s+(?:up|down)|turn\s+(?:the\s+)?brightness\s+(?:up|down)|(?:increase|decrease|raise|lower)\s+(?:the\s+)?brightness|dim\s+screen|brighten\s+screen)",
            "adjust_screen_brightness",
            extract_brightness_adjust
        )

        self.register_rule(
            r"(?:check|get|what\s+is\s+(?:the\s+)?|current\s+)?(?:screen\s+)?brightness",
            "get_screen_brightness",
            lambda m: {}
        )

        # 7. Window Management
        def extract_window_state(m: re.Match) -> Dict[str, Any]:
            return {"action": m.group(1), "window_name": m.group(2).strip()}

        self.register_rule(
            r"(minimize|maximize|restore)\s+(?:window\s+)?(.+)",
            "window_manage_state",
            extract_window_state
        )

        def extract_bring_front(m: re.Match) -> Dict[str, Any]:
            return {"window_name": m.group(1).strip()}

        self.register_rule(
            r"(?:switch\s+to|bring\s+(.+?)\s+(?:to\s+front|to\s+the\s+front|forward))",
            "window_bring_to_front",
            extract_bring_front
        )

        # 8. Media Controls
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

        # 9. Gmail Controls
        self.register_rule(
            r"(?:check|list|get|show|read)\s+(?:my\s+)?(?:emails|messages|inbox|mail)",
            "list_messages",
            lambda m: {"maxResults": 5}
        )
        self.register_rule(
            r"(?:check|list|get|show)\s+(?:my\s+)?(?:drafts|email\s+drafts)",
            "list_drafts",
            lambda m: {"maxResults": 5}
        )

    def register_rule(self, pattern: str, tool_name: str, extractor_fn):
        """Registers a new fast-path regex rule."""
        compiled = re.compile(pattern, re.IGNORECASE)
        self._rules.append((compiled, tool_name, extractor_fn))

    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Tests text against fast rules.
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
