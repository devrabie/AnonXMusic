# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import os
import time
import re
from typing import Union

from pyrogram import types as pytypes
from aiogram import types as aiotypes

from anony import app, config
from anony.helpers import Media, buttons, utils


class Telegram:
    def __init__(self):
        self.active = []
        self.events = {}
        self.last_edit = {}
        self.active_tasks = {}
        self.sleep = 5

    def get_media(self, msg: Union[pytypes.Message, aiotypes.Message]) -> bool:
        return any([
            getattr(msg, "video", None),
            getattr(msg, "audio", None),
            getattr(msg, "document", None),
            getattr(msg, "voice", None),
            getattr(msg, "video_note", None)
        ])

    async def cancel(self, query: Union[pytypes.CallbackQuery, aiotypes.CallbackQuery]):
        event = self.events.get(query.message.id)
        task = self.active_tasks.pop(query.message.id, None)
        if event:
            event.set()

        if task and not task.done():
            task.cancel()
        if event or task:
            await query.edit_message_text(
                query.lang["dl_cancel"].format(query.from_user.mention)
            )
        else:
            await query.answer(query.lang["dl_not_found"], show_alert=True)

    async def download(self, msg: Union[pytypes.Message, aiotypes.Message], sent: aiotypes.Message, lang: dict = None) -> Media | None:
        msg_id = sent.message_id if hasattr(sent, "message_id") else sent.id
        event = asyncio.Event()
        self.events[msg_id] = event
        self.last_edit[msg_id] = 0
        start_time = time.time()

        _lang = lang or getattr(sent, "lang", None) or {}

        # Detect message type
        is_aiogram = isinstance(msg, aiotypes.Message)

        if is_aiogram:
            media = msg.audio or msg.voice or msg.video or msg.document or msg.video_note
            file_id = getattr(media, "file_unique_id", None)
            file_name = getattr(media, "file_name", f"{file_id}")
            file_ext = file_name.split(".")[-1] if "." in file_name else "mp4"
            file_size = getattr(media, "file_size", 0)
            file_title = getattr(media, "title", None) or file_name
            duration = getattr(media, "duration", 0)
            mime_type = getattr(media, "mime_type", "")
            msg_link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.message_id}" if str(msg.chat.id).startswith("-100") else None
        else:
            media = msg.audio or msg.voice or msg.video or msg.document or msg.video_note
            file_id = getattr(media, "file_unique_id", None)
            file_name = getattr(media, "file_name", "")
            file_ext = file_name.split(".")[-1] if "." in file_name else "mp4"
            file_size = getattr(media, "file_size", 0)
            file_title = getattr(media, "title", None) or file_name or "Telegram File"
            duration = getattr(media, "duration", 0)
            mime_type = getattr(media, "mime_type", "")
            msg_link = msg.link

        video = bool(
            mime_type.startswith("video/") or
            file_name.lower().endswith((".mp4", ".mkv", ".mov", ".avi", ".webm")) or
            (is_aiogram and msg.video_note) or (not is_aiogram and msg.video_note)
        )

        if duration > config.DURATION_LIMIT:
            await sent.edit_text(_lang.get("play_duration_limit", "Limit").format(config.DURATION_LIMIT // 60))
            return None

        # Standard bot limit is 20MB for downloads unless using Local API
        if not config.API_SERVER and is_aiogram and file_size > 20 * 1024 * 1024:
             # If too big for bot and no local server, we can't download via bot
             # We should return None and let the caller try assistant
             return None

        if file_size > 2000 * 1024 * 1024: # 2GB hard limit
            await sent.edit_text(_lang.get("dl_limit", "Limit"))
            return None

        async def progress(current, total):
            if event.is_set():
                return

            now = time.time()
            if now - self.last_edit[msg_id] < self.sleep:
                return

            self.last_edit[msg_id] = now
            percent = (current * 100 / total) if total > 0 else 0
            speed = current / (now - start_time or 1e-6)
            eta = utils.format_eta(int((total - current) / speed)) if speed > 0 else "00:00"
            text = _lang.get("dl_progress", "Downloading...").format(
                utils.format_size(current),
                utils.format_size(total),
                percent,
                utils.format_size(speed),
                eta,
            )
            if config.API_SERVER and is_aiogram:
                 text += f"\n\n<b>Local API:</b> Active"

            try:
                await sent.edit_text(
                    text, reply_markup=buttons.cancel_dl(_lang.get("cancel", "Cancel"))
                )
            except Exception:
                pass

        try:
            file_path = f"downloads/{file_id}.{file_ext}"
            if not os.path.exists(file_path):
                if file_id in self.active:
                    await sent.edit_text(_lang.get("dl_active", "Active"))
                    return None

                self.active.append(file_id)

                if is_aiogram:
                    # Aiogram download
                    # We need to wrap progress for aiogram
                    async def aioprog(current, total, *args):
                        await progress(current, total)

                    task = asyncio.create_task(
                        app.download(media, destination=file_path, progress_callback=aioprog)
                    )
                else:
                    # Pyrogram download
                    task = asyncio.create_task(
                        msg.download(file_name=file_path, progress=progress)
                    )

                self.active_tasks[msg_id] = task
                await task
                if file_id in self.active: self.active.remove(file_id)
                self.active_tasks.pop(msg_id, None)
                await sent.edit_text(
                    _lang.get("dl_complete", "Done").format(round(time.time() - start_time, 2))
                )

            return Media(
                id=file_id,
                duration=time.strftime("%M:%S", time.gmtime(duration)),
                duration_sec=duration,
                file_path=file_path,
                message_id=msg_id,
                url=msg_link,
                title=file_title,
                video=video,
            )
        except asyncio.CancelledError:
            return None
        finally:
            self.events.pop(msg_id, None)
            self.last_edit.pop(msg_id, None)
            if file_id in self.active: self.active.remove(file_id)


    async def process_m3u8(self, url: str, msg_id: int, video: bool) -> Media:
        return Media(
            id=str(msg_id),
            file_path=url,
            message_id=msg_id,
            url=url,
            title="M3U8 Stream",
            video=video,
        )

    async def get_from_link(self, link: str, sent: aiotypes.Message, lang: dict = None) -> Media | None:
        try:
            link = link.strip()
            if "t.me/c/" in link:
                parts = link.split("/")
                chat = int("-100" + parts[-2])
                msg_id = int(parts[-1])
            else:
                parts = [p for p in link.split("/") if p]
                chat = parts[-2]
                if chat.replace("-", "").isdigit():
                    chat = int(chat) if chat.startswith("-") else int("-100" + chat)
                msg_id = int(parts[-1])
        except (IndexError, ValueError):
            return None

        msg = None
        # Try main bot first
        try:
            # We can't use app.get_messages (Aiogram Bot has no such method)
            # Use assistant instead or just skip app
            pass
        except Exception:
            pass

        # Try assistants if main bot failed
        if not msg or msg.empty:
            from anony import userbot
            for client in userbot.clients:
                try:
                    # Resolve peer before getting messages to avoid PeerIdInvalid/USERNAME_INVALID
                    try:
                        await client.resolve_peer(chat)
                    except Exception:
                        if isinstance(chat, str):
                            continue
                    msg = await client.get_messages(chat, msg_id)
                    if msg and not msg.empty:
                        break
                except Exception:
                    continue

        if not msg or msg.empty or not self.get_media(msg):
            return None

        return await self.download(msg, sent, lang)
