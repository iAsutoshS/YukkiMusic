#
# Copyright (C) 2024–2025
# TheTeamVivek@Github
# https://github.com/TheTeamVivek/YukkiMusic
# MIT License
#

import asyncio
import os
import re

from async_lru import alru_cache
from py_yt import VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from yt_dlp import YoutubeDL

import config
from YukkiMusic.utils.database import is_on_off
from YukkiMusic.utils.decorators import asyncify
from YukkiMusic.utils.formatters import seconds_to_min, time_to_seconds


NOTHING = {"cookies_dead": None}


# -------------------------------------------------------------------- #
# SHELL UTILS
# -------------------------------------------------------------------- #

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()

    if err:
        err = err.decode()
        if "unavailable videos are hidden" in err.lower():
            return out.decode()
        return err

    return out.decode()


# -------------------------------------------------------------------- #
# YOUTUBE CLASS
# -------------------------------------------------------------------- #

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # ------------------------------------------------------------ #

    async def exists(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    # ------------------------------------------------------------ #

    @property
    def use_fallback(self):
        return NOTHING["cookies_dead"] is True

    @use_fallback.setter
    def use_fallback(self, value):
        if NOTHING["cookies_dead"] is None:
            NOTHING["cookies_dead"] = value

    # ------------------------------------------------------------ #

    @asyncify
    def url(self, message: Message):
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        text = msg.text or msg.caption
                        return text[entity.offset : entity.offset + entity.length]

            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def details(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        search = VideosSearch(link, limit=1)
        result = (await search.next())["result"][0]

        duration_sec = (
            0 if not result["duration"]
            else int(time_to_seconds(result["duration"]))
        )

        return (
            result["title"],
            result["duration"],
            duration_sec,
            result["thumbnails"][0]["url"].split("?")[0],
            result["id"],
        )

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def title(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        search = VideosSearch(link, limit=1)
        return (await search.next())["result"][0]["title"]

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def duration(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        search = VideosSearch(link, limit=1)
        return (await search.next())["result"][0]["duration"]

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def thumbnail(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        search = VideosSearch(link, limit=1)
        return (await search.next())["result"][0]["thumbnails"][0]["url"].split("?")[0]

    # ------------------------------------------------------------ #

    async def video(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        cmd = [
            "yt-dlp",
            "--cookies-from-browser",
            "firefox",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        out, err = await proc.communicate()

        if out:
            return 1, out.decode().split("\n")[0]
        return 0, err.decode()

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def playlist(self, link, limit, videoid=None):
        if videoid:
            link = self.listbase + link
        link = link.split("&")[0]

        cmd = (
            f"yt-dlp -i --compat-options no-youtube-unavailable-videos "
            f"--get-id --flat-playlist --playlist-end {limit} "
            f'--skip-download "{link}" 2>/dev/null'
        )

        data = await shell_cmd(cmd)
        return [x for x in data.split("\n") if x]

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    async def track(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        try:
            search = VideosSearch(link, limit=1)
            res = (await search.next())["result"][0]

            return {
                "title": res["title"],
                "link": res["link"],
                "vidid": res["id"],
                "duration_min": res["duration"],
                "thumb": res["thumbnails"][0]["url"].split("?")[0],
            }, res["id"]

        except Exception:
            return await self._track(link)

    # ------------------------------------------------------------ #

    @asyncify
    def _track(self, query):
        opts = {
            "format": "best",
            "quiet": True,
            "noplaylist": True,
            "extract_flat": "in_playlist",
            "cookiesfrombrowser": ("firefox",),
        }

        with YoutubeDL(opts) as ydl:
            data = ydl.extract_info(f"ytsearch:{query}", download=False)
            entry = data["entries"][0]

            return {
                "title": entry["title"],
                "link": entry["url"],
                "vidid": entry["id"],
                "duration_min": (
                    seconds_to_min(entry["duration"])
                    if entry["duration"] else None
                ),
                "thumb": entry["thumbnails"][0]["url"],
            }, entry["id"]

    # ------------------------------------------------------------ #

    @alru_cache(maxsize=None)
    @asyncify
    def formats(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        opts = {
            "quiet": True,
            "cookiesfrombrowser": ("firefox",),
        }

        formats = []
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=False)
            for f in info["formats"]:
                if "dash" in str(f.get("format", "")).lower():
                    continue
                try:
                    formats.append({
                        "format": f["format"],
                        "filesize": f.get("filesize"),
                        "format_id": f["format_id"],
                        "ext": f["ext"],
                        "format_note": f.get("format_note"),
                        "yturl": link,
                    })
                except KeyError:
                    continue

        return formats, link

    # ------------------------------------------------------------ #
    # DOWNLOAD (FIXED)
    # ------------------------------------------------------------ #

    async def download(
        self,
        link: str,
        mystic,
        video=None,
        videoid=None,
        songaudio=None,
        songvideo=None,
        format_id=None,
        title=None,
    ):

        if videoid:
            link = self.base + link

        os.makedirs("downloads", exist_ok=True)

        # ---------------- AUDIO ---------------- #

        @asyncify
        def audio_dl():
            opts = {
                "format": "ba[abr>=180][abr<=360]/ba",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "0",
                }],
                "concurrent_fragment_downloads": 4,
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "prefer_ffmpeg": True,
                "cookiesfrombrowser": ("firefox",),
            }

            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.m4a")

        # ---------------- VIDEO ---------------- #

        @asyncify
        def video_dl():
            opts = {
                "format": "(b[height>=360][height<=1080]/bv*[height>=360][height<=1080]/bv*)+(ba[abr>=128]/ba)/b",
                "merge_output_format": "mp4",
                "concurrent_fragment_downloads": 4,
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "prefer_ffmpeg": True,
                "cookiesfrombrowser": ("firefox",),
            }

            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.mp4")

        # ---------------- ROUTER ---------------- #

        if video:
            if await is_on_off(config.YTDOWNLOADER):
                return await video_dl(), True

            cmd = [
                "yt-dlp",
                "--cookies-from-browser",
                "firefox",
                "-g",
                "-f",
                "best",
                link,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            out, _ = await proc.communicate()
            if out:
                return out.decode().split("\n")[0], None

            return await video_dl(), True

        return await audio_dl(), True
