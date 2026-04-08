# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import types

from anony import app, config, lang
from anony.core.lang import lang_codes


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(
                [self.ikb(text=timer, callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="▷", callback_data=f"controls resume {chat_id}"),
                    self.ikb(text="II", callback_data=f"controls pause {chat_id}"),
                    self.ikb(text="⥁", callback_data=f"controls replay {chat_id}"),
                    self.ikb(text="‣‣I", callback_data=f"controls skip {chat_id}"),
                    self.ikb(text="▢", callback_data=f"controls stop {chat_id}"),
                ]
            )

        # Add Dashboard link to controls if private or if we want easier access
        keyboard.append([self.ikb(text="📊 Dashboard", callback_data="manage_chats")])

        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text=_lang["back"], callback_data="help back"),
                    self.ikb(text=_lang["main_menu"], callback_data="start_back"),
                ]
            ]
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            buttons = [
                self.ikb(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
                for i, cb in enumerate(cbs)
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
            rows.append([self.ikb(text=_lang["back"], callback_data="start_back")])

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}"
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=admin_only, callback_data="settings play"),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=cmd_delete, callback_data="settings delete"),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def admin_panel_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text=_lang["manage_assistants"], callback_data="manage_ass"),
                ],
                [
                    self.ikb(text=_lang["stats_fetching"], callback_data="stats"),
                    self.ikb(text=_lang["main_menu"], callback_data="start_back"),
                ],
            ]
        )

    def assistants_markup(self, _lang: dict, assistants: list) -> types.InlineKeyboardMarkup:
        buttons = [
            [self.ikb(text=f"🗑️ @{u.username}" if u.username else u.first_name, callback_data=f"del_ass {u.id}")]
            for u in assistants
        ]
        buttons.append([self.ikb(text=_lang["add_assistant"], callback_data="add_ass")])
        buttons.append([self.ikb(text=_lang["back"], callback_data="admin_panel")])
        return self.ikm(buttons)

    def dashboard_markup(self, _lang: dict, chats: list) -> types.InlineKeyboardMarkup:
        buttons = []
        for chat_id, title in chats:
            buttons.append([self.ikb(text=title, callback_data=f"manage_chat {chat_id}")])

        buttons.append([
            self.ikb(text=_lang["add_group"], url=f"https://t.me/{app.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats"),
            self.ikb(text=_lang["add_channel"], url=f"https://t.me/{app.username}?startchannel=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats"),
        ])
        buttons.append([self.ikb(text=_lang["add_chat_manual"], callback_data="add_chat_manual")])
        buttons.append([self.ikb(text=_lang["main_menu"], callback_data="start_back")])
        return self.ikm(buttons)

    def cancel_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=_lang["cancel"], callback_data="start_back")]])

    def stream_markup(self, _lang: dict, chat_id: int, status: bool, stype: str = "audio", source: str = "url") -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text=_lang["stream_status"] + (": ON" if status else ": OFF"), callback_data="none"),
                ],
                [
                    self.ikb(text=_lang["stream_type"] + (": 🎧" if stype == "audio" else ": 📺"), callback_data=f"toggle_stype {chat_id}"),
                    self.ikb(text=_lang["stream_source"] + (": 🔗" if source == "url" else ": 📑"), callback_data=f"toggle_source {chat_id}"),
                ],
                [
                    self.ikb(
                        text=_lang["stop_stream"] if status else _lang["start_stream"],
                        callback_data=f"toggle_stream {chat_id}",
                    ),
                ],
                [
                    self.ikb(text=_lang["set_url"], callback_data=f"set_url {chat_id}"),
                    self.ikb(text=_lang["add_local_media"], callback_data=f"add_local {chat_id}"),
                ],
                [
                    self.ikb(text=_lang["back"], callback_data="manage_chats"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False, user_id: int = None
    ) -> types.InlineKeyboardMarkup:
        if private:
            rows = [
                [
                    self.ikb(text=lang["add_group"], url=f"https://t.me/{app.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats"),
                    self.ikb(text=lang["add_channel"], url=f"https://t.me/{app.username}?startchannel=true&admin=post_messages+edit_messages+delete_messages+add_admins+invite_users+manage_video_chats"),
                ],
                [
                    self.ikb(text=lang["my_chats"], callback_data="manage_chats"),
                    self.ikb(text=lang["help"], callback_data="help"),
                ],
            ]
            if user_id and user_id == app.owner:
                rows.append([self.ikb(text=lang["admin_panel"], callback_data="admin_panel")])
        else:
            rows = [
                [
                    self.ikb(text=lang["help"], callback_data="help"),
                ]
            ]

        if not private:
            rows += [[self.ikb(text=lang["language"], callback_data="language")]]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
