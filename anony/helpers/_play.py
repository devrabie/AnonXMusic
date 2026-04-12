# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import html
from aiogram import types, enums, F
from pyrogram import enums as pyenums, errors

from anony import app, config, db, logger
from . import utils


async def process_play(m: types.Message, lang: dict, chat_id: int, command: str, video: bool, force: bool, url: str = None):
    from anony import tg, yt, anon, queue
    # If no URL, try to get from message (reply or text)
    if not url:
        url = utils.get_url(m)

    # Fallback for manual link extraction if utils.get_url fails (e.g. from callback command)
    if not url and command:
        for word in command.split():
            if word.startswith("http"):
                url = word
                break

    media = None
    if m.reply_to_message and (m.reply_to_message.audio or m.reply_to_message.video or m.reply_to_message.document or m.reply_to_message.voice or m.reply_to_message.video_note):
        sent = await m.reply(lang["play_downloading"])
        # Bridge aiogram and pyrogram for download via assistant
        from anony import userbot
        client = userbot.clients[0] if userbot.clients else None
        if not client:
             return await sent.edit_text(lang["play_no_assistant"])

        try:
            # We need the pyrogram message object. We can try to get it by ID
            # But the assistant might not be in the chat where the reply is.
            # Usually, for replies, we assume it's in the same chat.
            try:
                p_msg = await client.get_messages(m.chat.id, m.reply_to_message.message_id)
            except Exception:
                fwd = await m.reply_to_message.forward(client.id)
                p_msg = await client.get_messages(client.id, fwd.message_id)
            media = await tg.download(p_msg, sent, lang)
        except Exception as e:
            return await sent.edit_text(f"Error: {e}")
    elif url:
        if "t.me/" in url:
            sent = await m.reply(lang["play_searching"])
            media = await tg.get_from_link(url, sent, lang)
            if not media:
                return await sent.edit_text(lang["play_not_found"].format(config.SUPPORT_CHAT))
            await sent.delete()
        else:
            return await m.reply(lang["yt_disabled"])
    else:
        # Search is disabled as per user instruction if it's for YouTube
        # But user mentioned "playing through search in the channel playlist"
        # For now, let's just return yt_disabled if it's not a link/reply
        return await m.reply(lang["yt_disabled"])

    if not media:
        return

    # Check duration if available
    duration_sec = getattr(media, "duration_sec", 0)
    if duration_sec > config.DURATION_LIMIT:
        return await m.reply(lang["play_duration_limit"].format(config.DURATION_LIMIT_MIN))

    media.user = m.from_user.mention_html()

    if force:
        await anon.stop(chat_id)

    position = await queue.add(chat_id, media)
    if position == -2:
        return await m.reply(lang["play_duplicate"])

    if position == 0 and not await db.get_call(chat_id):
        if not await join_assistant(chat_id, lang, m):
            return
        queue._played[chat_id] = 0
        await anon.play_media(chat_id, m if m.chat.id == chat_id else None, media)
        if m.chat.id != chat_id:
             is_paused = await db.is_paused(chat_id)
             await m.reply(
                 lang["play_started"].format(html.escape(media.title), chat_id),
                 reply_markup=buttons.controls(chat_id, is_paused=is_paused)
             )
    else:
        await m.reply(
            lang["play_queued"].format(
                position + 1,
                media.url or "#",
                html.escape(media.title),
                media.duration,
                m.from_user.mention_html(),
            ),
            disable_web_page_preview=True
        )


async def join_assistant(chat_id: int, lang: dict, m: types.Message = None):
    client = await db.get_client(chat_id)
    if not client:
        if m: await m.reply(lang["play_no_assistant"])
        return False

    # Resolve peer to avoid PeerIdInvalid
    try:
        await client.resolve_peer(chat_id)
    except Exception:
        try:
            await client.get_chat(chat_id)
        except Exception:
            pass

    try:
        member = await client.get_chat_member(chat_id, client.id)
        if member.status in [
            pyenums.ChatMemberStatus.BANNED,
            pyenums.ChatMemberStatus.RESTRICTED,
        ]:
            try:
                await app.unban_chat_member(
                    chat_id=chat_id, user_id=client.id, only_if_banned=True
                )
            except Exception:
                if m: await m.reply(
                    lang["play_banned"].format(
                        app.name,
                        client.id,
                        client.mention,
                        f"@{client.username}" if client.username else None,
                    )
                )
                return False
    except Exception:
        chat = await app.get_chat(chat_id)
        if chat.username:
            invite_link = chat.username
        else:
            try:
                invite_link = chat.invite_link or await app.export_chat_invite_link(chat_id)
            except Exception as ex:
                if m: await m.reply(
                    lang["play_invite_error"].format(type(ex).__name__)
                )
                return False

        umm = None
        if m: umm = await m.reply(lang["play_invite"].format(app.name))
        await asyncio.sleep(2)
        try:
            await client.join_chat(invite_link)
        except (getattr(errors, "InviteHashExpired", errors.Forbidden), getattr(errors, "InviteHashInvalid", errors.Forbidden)):
            try:
                invite_link = await app.export_chat_invite_link(chat_id)
                await client.join_chat(invite_link)
            except Exception as ex:
                if umm: await umm.edit_text(
                    lang["play_invite_error"].format(type(ex).__name__)
                )
                return False
        except errors.UserAlreadyParticipant:
            pass
        except Exception as ex:
            logger.error(f"Error joining chat - {chat_id}: {ex}")
            if umm: await umm.edit_text(
                lang["play_invite_error"].format(type(ex).__name__)
            )
            return False

        if umm: await umm.delete()

    # Crucial: Always force peer caching after join or even if already in chat
    # This resolves PeerIdInvalid for in_memory sessions
    try:
        await client.get_chat(chat_id)
    except Exception:
        try:
            await client.resolve_peer(chat_id)
        except Exception:
            pass

    # Ensure assistant is promoted
    chat = await app.get_chat(chat_id)
    if chat.type in [enums.ChatType.CHANNEL, enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            from aiogram.enums import ChatMemberStatus
            member = await app.get_chat_member(chat_id, client.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                await app.promote_chat_member(
                    chat_id=chat_id, user_id=client.id,
                    can_manage_video_chats=True,
                    can_invite_users=True,
                )
        except Exception:
            pass
    return True


def checkUB(play):
    async def wrapper(event: types.Message, lang: dict, *args, **kwargs):
        from anony import queue, yt
        m = event
        if not m.from_user:
            return await m.reply(lang["play_user_invalid"])

        chat_id = m.chat.id
        if m.chat.type not in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP, enums.ChatType.CHANNEL, enums.ChatType.PRIVATE]:
            await m.reply(lang["play_chat_invalid"])
            try:
                return await m.bot.leave_chat(chat_id)
            except:
                return

        if m.chat.type == enums.ChatType.PRIVATE:
            return await play(event, lang, False, False, False, None)

        command = m.text.split()
        if not m.reply_to_message and (
            len(command) < 2 or (len(command) == 2 and command[1] == "-f")
        ):
            return await m.reply(lang["play_usage"])

        if len(queue.get_queue(chat_id)) >= config.QUEUE_LIMIT:
            return await m.reply(lang["play_queue_full"].format(config.QUEUE_LIMIT))

        force = command[0].endswith("force") or (
            len(command) > 1 and "-f" in command[1]
        )
        video = command[0][1] == "v" if len(command[0]) > 1 else False
        video = video and config.VIDEO_PLAY

        url = utils.get_url(m)
        if url and yt.invalid(url):
            return await m.reply(lang["play_not_found"].format(config.SUPPORT_CHAT))
        m3u8 = url and not yt.valid(url)

        play_mode = await db.get_play_mode(chat_id)
        if play_mode or force:
            adminlist = await db.get_admins(chat_id)
            if (
                m.from_user.id not in adminlist
                and not await db.is_auth(chat_id, m.from_user.id)
                and str(m.from_user.id) != str(app.owner)
            ):
                return await m.reply(lang["play_admin"])

        if chat_id not in db.active_calls:
            if not await join_assistant(chat_id, lang, m):
                return

        if await db.get_cmd_delete(chat_id):
            try:
                await m.delete()
            except Exception:
                pass

        return await play(event, lang, force, m3u8, video, url)

    return wrapper
