# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from anony import app, config, lang
from anony.core.lang import lang_codes


class Inline:
    def __init__(self):
        pass

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=text, callback_data="cancel_dl")
        return builder.as_markup()

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if status:
            builder.button(text=status, callback_data=f"controls status {chat_id}")
            builder.adjust(1)
        elif timer:
            builder.button(text=timer, callback_data=f"controls status {chat_id}")
            builder.adjust(1)

        if not remove:
            builder.button(text="▷", callback_data=f"controls resume {chat_id}")
            builder.button(text="II", callback_data=f"controls pause {chat_id}")
            builder.button(text="⥁", callback_data=f"controls replay {chat_id}")
            builder.button(text="‣‣I", callback_data=f"controls skip {chat_id}")
            builder.button(text="▢", callback_data=f"controls stop {chat_id}")
            builder.adjust(5 if not (status or timer) else 1, 5)

        builder.button(text="📊 Dashboard", callback_data="manage_chats")
        builder.adjust(1) if remove else None

        return builder.as_markup()

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if back:
            builder.button(text=_lang["back"], callback_data="help back")
            builder.button(text=_lang["main_menu"], callback_data="start_back")
            builder.adjust(2)
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            for i, cb in enumerate(cbs):
                builder.button(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
            builder.adjust(3)
            builder.row(types.InlineKeyboardButton(text=_lang["back"], callback_data="start_back"))

        return builder.as_markup()

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()
        builder = InlineKeyboardBuilder()
        for code, name in langs.items():
            builder.button(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
        builder.adjust(2)
        return builder.as_markup()

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=text, url=config.SUPPORT_CHAT)
        return builder.as_markup()

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=_text, callback_data=f"controls force {chat_id} {item_id}")
        return builder.as_markup()

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        _action = "pause" if playing else "resume"
        builder.button(text=_text, callback_data=f"controls {_action} {chat_id} q")
        return builder.as_markup()

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=lang["play_mode"] + " ➜", callback_data="settings")
        builder.button(text=str(admin_only), callback_data="settings play")
        builder.button(text=lang["cmd_delete"] + " ➜", callback_data="settings")
        builder.button(text=str(cmd_delete), callback_data="settings delete")
        builder.button(text=lang["language"] + " ➜", callback_data="settings")
        builder.button(text=lang_codes[language], callback_data="language")
        builder.adjust(2)
        return builder.as_markup()

    def admin_panel_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=_lang["manage_assistants"], callback_data="manage_ass")
        builder.button(text=_lang["stats_fetching"], callback_data="stats")
        builder.button(text=_lang["main_menu"], callback_data="start_back")
        builder.adjust(1, 2)
        return builder.as_markup()

    def assistants_markup(self, _lang: dict, assistants: list) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for u in assistants:
            # Handle both Pyrogram Client and User objects (assistants are Pyrogram)
            username = getattr(u, "username", None) or getattr(getattr(u, "me", None), "username", None)
            first_name = getattr(u, "first_name", None) or getattr(getattr(u, "me", None), "first_name", "Assistant")
            user_id = getattr(u, "id", None) or getattr(getattr(u, "me", None), "id", 0)

            builder.button(text=f"🗑️ @{username}" if username else first_name, callback_data=f"del_ass {user_id}")

        builder.button(text=_lang["add_assistant"], callback_data="add_ass")
        builder.button(text=_lang["back"], callback_data="admin_panel")
        builder.adjust(1)
        return builder.as_markup()

    def dashboard_markup(self, _lang: dict, chats: list) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for chat_id, title in chats:
            builder.button(text=title, callback_data=f"manage_chat {chat_id}")
        builder.adjust(1)

        builder.row(
            types.InlineKeyboardButton(text=_lang["add_group"], url=f"https://t.me/{app.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats"),
            types.InlineKeyboardButton(text=_lang["add_channel"], url=f"https://t.me/{app.username}?startchannel=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats")
        )
        builder.row(types.InlineKeyboardButton(text=_lang["add_chat_manual"], callback_data="add_chat_manual"))
        builder.row(types.InlineKeyboardButton(text=_lang["main_menu"], callback_data="start_back"))
        return builder.as_markup()

    def cancel_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=_lang["cancel"], callback_data="start_back")
        return builder.as_markup()

    def play_chat_markup(self, _lang: dict, chats: list, command: str) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for chat_id, title in chats:
            builder.button(text=title, callback_data=f"play_target {chat_id} {command}")
        builder.adjust(1)
        builder.row(types.InlineKeyboardButton(text=_lang["back"], callback_data="start_back"))
        return builder.as_markup()

    def stream_markup(self, _lang: dict, chat_id: int, status: bool, stype: str = "audio", source: str = "url") -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=_lang["stream_status"] + (": ON" if status else ": OFF"), callback_data="none")
        builder.button(text=_lang["stream_type"] + (": 🎧" if stype == "audio" else ": 📺"), callback_data=f"toggle_stype {chat_id}")
        builder.button(text=_lang["stream_source"] + (": 🔗" if source == "url" else ": 📑"), callback_data=f"toggle_source {chat_id}")
        builder.button(
            text=_lang["stop_stream"] if status else _lang["start_stream"],
            callback_data=f"toggle_stream {chat_id}",
        )
        builder.button(text=_lang["set_url"], callback_data=f"set_url {chat_id}")
        builder.button(text=_lang["add_local_media"], callback_data=f"add_local {chat_id}")
        builder.button(text=_lang["playlist_management"], callback_data=f"manage_playlist {chat_id}")
        builder.button(text=_lang["back"], callback_data="manage_chats")
        builder.adjust(1, 2, 1, 2, 1, 1)
        return builder.as_markup()

    def playlist_markup(self, _lang: dict, chat_id: int, queue_list: list) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for i, item in enumerate(queue_list):
            builder.button(text=f"{i+1}. {item.title[:20]}", callback_data=f"play_item {chat_id} {i}")
            builder.button(text="🗑️", callback_data=f"del_item {chat_id} {i}")

        builder.adjust(2)
        builder.row(types.InlineKeyboardButton(text=_lang["clear_queue"], callback_data=f"clear_queue {chat_id}"))
        builder.row(types.InlineKeyboardButton(text=_lang["back"], callback_data=f"manage_chat {chat_id}"))
        return builder.as_markup()

    def start_key(
        self, lang: dict, private: bool = False, user_id: int = None
    ) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if private:
            builder.button(text=lang["add_group"], url=f"https://t.me/{app.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats")
            builder.button(text=lang["add_channel"], url=f"https://t.me/{app.username}?startchannel=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats")
            builder.button(text=lang["my_chats"], callback_data="manage_chats")
            builder.button(text=lang["help"], callback_data="help")
            if user_id and str(user_id) == str(app.owner):
                builder.button(text=lang["admin_panel"], callback_data="admin_panel")
            builder.adjust(2, 2, 1)
        else:
            builder.button(text=lang["help"], callback_data="help")
            builder.button(text=lang["language"], callback_data="language")
            builder.adjust(1)
        return builder.as_markup()

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        # builder.button(text="❐", copy_text=link) # aiogram might need different way for copy_text if supported
        builder.button(text="Youtube", url=link)
        return builder.as_markup()
