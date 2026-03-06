"""
discord_sender.py
Uploads a clip to a Discord channel via bot API.
Uses discord.py to connect as a bot and send the file.
"""

import os
import asyncio
import discord
from discord import File

_MAX_BYTES = 25 * 1024 * 1024  # 25 MB Discord free tier upload limit


def send(
    bot_token: str,
    channel_id: str,
    file_path: str,
    caption: str = "",
) -> tuple[bool, str]:
    """
    Synchronous wrapper that runs the async Discord bot upload.
    caption is posted as message text above the attached file (optional).
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

    result = {"success": False, "msg": ""}

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            channel = client.get_channel(ch_id)
            if not channel:
                result["msg"] = f"Channel {ch_id} not found — check channel ID."
                return

            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                await channel.send(
                    content=caption if caption else None,
                    file=File(f, filename=filename),
                )

            result["success"] = True
            result["msg"] = f"Uploaded to Discord: {filename}"
        except Exception as e:
            result["msg"] = f"Discord upload error: {e}"
        finally:
            await client.close()

    try:
        # client.run() handles the event loop and blocks until client.close()
        client.run(bot_token.strip(), log_handler=None)
        return result["success"], result["msg"]
    except discord.LoginFailure:
        return False, "Discord bot token invalid — check your token in Settings."
    except Exception as e:
        return False, f"Discord error: {e}"
