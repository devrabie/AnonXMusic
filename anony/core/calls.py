# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import html
from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
from pyrogram import errors, types as pytypes
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import (app, config, db, lang, logger,
                   userbot, yt)
from anony.helpers import Media, Track, buttons


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def stop(self, chat_id: int) -> None:
        from anony import queue
        client = await db.get_assistant(chat_id)
        # We don't clear the queue anymore as per user request for permanent playlists
        # await queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, False)
        queue._played[chat_id] = 0

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: any, # Can be aiogram message or None
        media: Media | Track = None,
        seek_time: int = 0,
        stream_url: str = None,
        video: bool = False,
    ) -> None:
        from anony import thumb
        client = await db.get_assistant(chat_id)
        ub = await db.get_client(chat_id)
        if not ub:
            logger.error(f"No MTProto client found for assistant in chat {chat_id}")
            return

        assistant_id = getattr(ub, "id", None)
        if not assistant_id:
            try:
                me = getattr(ub, "me", None) or await ub.get_me()
                assistant_id = me.id
                ub.id = assistant_id
            except Exception as e:
                logger.error(f"Could not retrieve assistant ID: {e}")
                return

        # Resolve peer to avoid PeerIdInvalid
        try:
            await ub.get_chat(chat_id)
        except Exception:
            try:
                await ub.resolve_peer(chat_id)
            except Exception:
                pass

        # Ensure assistant is in chat and promoted
        try:
            member = await app.get_chat_member(chat_id, assistant_id)
            # member here is aiogram member
            from aiogram.enums import ChatMemberStatus
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                try:
                    # Promote via aiogram app
                    await app.promote_chat_member(
                        chat_id=chat_id, user_id=assistant_id,
                        can_manage_video_chats=True,
                        can_invite_users=True,
                    )
                except Exception:
                    pass
        except Exception:
            try:
                chat = await app.get_chat(chat_id)
                if chat.username:
                    invite_link = chat.username
                else:
                    invite_link = chat.invite_link or await app.export_chat_invite_link(chat_id)

                try:
                    await ub.join_chat(invite_link)
                except (getattr(errors, "InviteHashExpired", errors.Forbidden), getattr(errors, "InviteHashInvalid", errors.Forbidden)):
                    invite_link = await app.export_chat_invite_link(chat_id)
                    await ub.join_chat(invite_link)

                await app.promote_chat_member(
                    chat_id=chat_id, user_id=assistant_id,
                    can_manage_video_chats=True,
                    can_invite_users=True,
                )
            except Exception as e:
                logger.error(f"Assistant failed to join/promote in {chat_id}: {e}")

        _lang = await lang.get_lang(chat_id)

        if stream_url:
            media = Track(
                id="live",
                title="Live Stream",
                duration="Live",
                url=stream_url,
                file_path=stream_url,
                video=video,
                user="System"
            )
            _thumb = config.DEFAULT_THUMB if config.THUMB_GEN else None
        else:
            _thumb = (
                await thumb.generate(media)
                if isinstance(media, Track)
                else config.DEFAULT_THUMB
            ) if config.THUMB_GEN else None

        if not media.file_path:
            if message:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        if stream_url:
            stream = types.MediaStream(
                media_path=stream_url,
                audio_parameters=types.AudioQuality.HIGH,
                video_parameters=types.VideoQuality.HD_720p,
                audio_flags=types.MediaStream.Flags.REQUIRED,
                video_flags=(
                    types.MediaStream.Flags.REQUIRED
                    if video
                    else types.MediaStream.Flags.IGNORE
                ),
            )
        else:
            stream = types.MediaStream(
                media_path=media.file_path,
                audio_parameters=types.AudioQuality.HIGH,
                video_parameters=types.VideoQuality.HD_720p,
                audio_flags=types.MediaStream.Flags.REQUIRED,
                video_flags=(
                    types.MediaStream.Flags.REQUIRED
                    if media.video
                    else types.MediaStream.Flags.IGNORE
                ),
                ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
            )
        try:
            try:
                await client.play(
                    chat_id=chat_id,
                    stream=stream,
                    config=types.GroupCallConfig(auto_start=True),
                )
            except exceptions.NoVideoSourceFound:
                # Fallback to audio only
                # Re-create the stream without video to avoid AttributeError
                stream = types.MediaStream(
                    media_path=stream_url if stream_url else media.file_path,
                    audio_parameters=types.AudioQuality.HIGH,
                    video_parameters=types.VideoQuality.HD_720p,
                    audio_flags=types.MediaStream.Flags.REQUIRED,
                    video_flags=types.MediaStream.Flags.IGNORE,
                    ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
                )
                await client.play(
                    chat_id=chat_id,
                    stream=stream,
                    config=types.GroupCallConfig(auto_start=True),
                )

            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    html.escape(media.title),
                    media.duration,
                    media.user,
                )
                is_paused = await db.is_paused(chat_id)
                keyboard = buttons.controls(chat_id, is_paused=is_paused)

                if message:
                    try:
                        if _thumb:
                            from aiogram.types import InputMediaPhoto, FSInputFile, URLInputFile
                            if isinstance(_thumb, str):
                                _input_thumb = URLInputFile(_thumb) if _thumb.startswith("http") else FSInputFile(_thumb)
                            else:
                                _input_thumb = _thumb
                            await message.edit_media(
                                media=InputMediaPhoto(
                                    media=_input_thumb,
                                    caption=text,
                                ),
                                reply_markup=keyboard,
                            )
                        else:
                            await message.edit_text(text, reply_markup=keyboard)
                        return
                    except Exception:
                        pass

                if _thumb:
                    from aiogram.types import FSInputFile, URLInputFile
                    if isinstance(_thumb, str):
                        _input_thumb = URLInputFile(_thumb) if _thumb.startswith("http") else FSInputFile(_thumb)
                    else:
                        _input_thumb = _thumb
                    sent = await app.send_photo(
                        chat_id=chat_id,
                        photo=_input_thumb,
                        caption=text,
                        reply_markup=keyboard,
                    )
                else:
                    sent = await app.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                    )
                media.message_id = sent.message_id
        except FileNotFoundError:
            if message:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            if message:
                await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_rtmp"])


    async def replay(self, chat_id: int) -> None:
        from anony import queue
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if not media:
            return

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.message_id
        await self.play_media(chat_id, msg, media)


    async def play_prev(self, chat_id: int) -> None:
        from anony import queue
        media = await queue.get_prev(chat_id)
        try:
            if media and media.message_id:
                await app.delete_message(
                    chat_id=chat_id,
                    message_id=media.message_id,
                )
                media.message_id = 0
        except Exception:
            pass

        if not media:
            return await self.stop(chat_id)

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.play_next(chat_id)
                return await msg.edit_text(
                    _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.message_id
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        from anony import queue
        media = await queue.get_next(chat_id)
        try:
            if media.message_id:
                await app.delete_message(
                    chat_id=chat_id,
                    message_id=media.message_id,
                )
                media.message_id = 0
        except Exception:
            pass

        if not media:
            return await self.stop(chat_id)

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.play_next(chat_id)
                return await msg.edit_text(
                    _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.message_id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients if hasattr(client, 'ping')]
        if not pings: return 0.0
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls) -> None:
        ub = getattr(client, "app", getattr(client, "_app", None))
        if ub:
            assistant_id = getattr(ub, "id", None)
            if not assistant_id:
                try:
                    me = getattr(ub, "me", None) or await ub.get_me()
                    assistant_id = me.id
                    ub.id = assistant_id
                except Exception:
                    assistant_id = None
            client.id = assistant_id

        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    chat_id = update.chat_id
                    url, status, stype, source = await db.get_stream(chat_id)
                    if status:
                        if source == "url" and url:
                            try:
                                return await self.play_media(chat_id, None, stream_url=url, video=(stype == "video"))
                            except Exception as e:
                                logger.error(f"Failed to auto-restart stream in {chat_id}: {e}")
                        elif source == "playlist":
                            return await self.play_next(chat_id)
                    await self.play_next(chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")

        # Auto-restart active streams
        active_streams = await db.get_active_streams()
        for chat_id, url, stype, source in active_streams:
            try:
                if source == "url":
                    await self.play_media(chat_id, None, stream_url=url, video=(stype == "video"))
                else:
                    await self.play_next(chat_id)
                logger.info(f"Auto-restarted stream in {chat_id}")
            except Exception as e:
                logger.error(f"Failed to auto-restart stream in {chat_id}: {e}")
