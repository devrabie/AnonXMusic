# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from aiogram import types, enums, F
from pyrogram import enums as pyenums, errors

from anony import app, config, db, logger
from . import utils


async def join_assistant(chat_id: int, lang: dict, m: types.Message = None):
    client = await db.get_client(chat_id)
    if not client:
        if m: await m.reply(lang["play_no_assistant"])
        return False

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
        try:
            await client.resolve_peer(chat_id)
        except:
            pass

    # Ensure assistant is promoted if in channel
    chat = await app.get_chat(chat_id)
    if chat.type == enums.ChatType.CHANNEL:
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
