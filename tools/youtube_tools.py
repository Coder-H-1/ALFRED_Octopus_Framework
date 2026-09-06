"""
FmWk/tools/youtube_tools.py — Native In-Process YouTube Streaming Tools
"""

from typing import Dict, Any
from ..core.decorators import mcp_tool


@mcp_tool(
    name="youtube_play",
    description="Search and play a video or music track from YouTube by song/video name or query.",
    category="media"
)
def youtube_play(query: str) -> Dict[str, Any]:
    """Searches YouTube using lazy-loaded yt_dlp and pushes stream to GUI player."""
    try:
        # Lazy load heavy yt_dlp to preserve memory until user requests playback
        import yt_dlp
        from FILES.gui_controller import show_data

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'default_search': 'ytsearch5'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = [e for e in info.get('entries', []) if e]

            if not entries:
                return {"error": f"I couldn't find any videos for '{query}', sir."}

            embeddable = None
            direct_url = None

            for entry in entries:
                v_id = entry.get('id')
                if entry.get('playable_in_embed') is not False and v_id:
                    embeddable = entry
                    break
                elif not direct_url and entry.get('url'):
                    direct_url = entry.get('url')

            if embeddable:
                v_id = embeddable.get('id')
                title = embeddable.get('title', query)
                show_data([f"youtube:{v_id}"])
                return {
                    "status": f"Playing '{title}' from YouTube, sir.",
                    "keep_ui": True,
                    "video_id": v_id,
                    "title": title
                }
            elif direct_url:
                show_data([f"video:{direct_url}"])
                return {
                    "status": f"Playing direct stream for '{query}', sir.",
                    "keep_ui": True,
                    "direct_url": direct_url
                }
            elif entries[0].get('id'):
                v_id = entries[0]['id']
                show_data([f"youtube:{v_id}"])
                return {
                    "status": f"Playing '{query}' from YouTube, sir.",
                    "keep_ui": True,
                    "video_id": v_id
                }
            else:
                return {"error": "Could not extract a playable stream for that video."}

    except Exception as e:
        return {"error": f"YouTube playback failed: {e}"}


@mcp_tool(
    name="youtube_stop",
    description="Stop active YouTube video playback and close player.",
    category="media"
)
def youtube_stop() -> Dict[str, Any]:
    """Clears the video stream from the GUI."""
    try:
        from FILES.gui_controller import show_data
        show_data([])
        return {"status": "Stopped YouTube playback, sir."}
    except Exception as e:
        return {"error": f"Failed to stop playback: {e}"}


_YOUTUBE_VOLUME = 100

@mcp_tool(
    name="youtube_set_volume",
    description="Set YouTube playback volume level from 0 to 100 percent.",
    category="media"
)
def youtube_set_volume(level: int) -> Dict[str, Any]:
    """Sets YouTube volume level."""
    global _YOUTUBE_VOLUME
    target = max(0, min(100, int(level)))
    _YOUTUBE_VOLUME = target
    return {"status": f"YouTube volume set to {target}%, sir.", "volume": target}

