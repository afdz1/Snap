"""
discord_sender.py
Uploads a clip (or screenshot) to a Discord channel via the REST API.
Uses aiohttp directly — no discord.py Client, no event loop conflicts.
"""

import os
import ssl
import asyncio
import certifi
import aiohttp

_MAX_BYTES   = 25 * 1024 * 1024          # 25 MB Discord free-tier limit
_API_BASE    = "https://discord.com/api/v10"


async def _upload(
    bot_token: str,
    ch_id: int,
    file_path: str,
    caption: str,
) -> tuple[bool, str]:
    """Async core: POST the file to Discord's channel messages endpoint."""
    # Connector is created inside the running event loop — no 'no running event
    # loop' error, and certifi's CA bundle fixes SSL issues in frozen exes.
    ssl_ctx   = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)

    headers = {"Authorization": f"Bot {bot_token}"}
    url     = f"{_API_BASE}/channels/{ch_id}/messages"

    async with aiohttp.ClientSession(connector=connector) as session:
        with open(file_path, "rb") as fh:
            form = aiohttp.FormData()
            if caption:
                form.add_field("content", caption)
            form.add_field(
                "file",
                fh,
                filename=os.path.basename(file_path),
            )
            async with session.post(url, headers=headers, data=form) as resp:
                if resp.status in (200, 201):
                    return True, f"Uploaded to Discord: {os.path.basename(file_path)}"
                text = await resp.text()
                return False, f"Discord API error {resp.status}: {text}"


def send(
    bot_token: str,
    channel_id: str,
    file_path: str,
    caption: str = "",
) -> tuple[bool, str]:
    """
    Synchronous wrapper — safe to call from any thread.
    Returns (success: bool, message: str).
    """
    if not bot_token or not bot_token.strip():
        return False, "No Discord bot token configured — skipping upload."

    if not channel_id or not channel_id.strip():
        return False, "No Discord channel ID configured — skipping upload."

    try:
        ch_id = int(channel_id.strip())
    except ValueError:
        return False, "Discord channel ID must be a number — check Settings."

    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    size = os.path.getsize(file_path)
    if size > _MAX_BYTES:
        mb = size / 1024 / 1024
        return False, f"File too large ({mb:.1f} MB > 25 MB limit) — skipping upload."

    try:
        return asyncio.run(_upload(bot_token.strip(), ch_id, file_path, caption))
    except Exception as exc:
        return False, f"Discord upload error: {exc}"
