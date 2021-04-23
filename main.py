#!/usr/bin/env python3.8
import asyncio
import json
import logging
import os
from datetime import datetime

import aiohttp
import asyncpg
import discord
import discord_slash
import websockets
from discord.ext import commands
from discord.ext.commands.bot import _default as bot_default
from dotenv import load_dotenv

import common.classes as custom_classes
import common.configs as configs
import common.star_classes as star_classes
import common.utils as utils

load_dotenv()

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename=os.environ.get("LOG_FILE_PATH"), encoding="utf-8", mode="w"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


def seraphim_prefixes(bot: commands.Bot, msg: discord.Message):
    mention_prefixes = [f"{bot.user.mention} ", f"<@!{bot.user.id}> "]

    try:
        custom_prefixes = bot.config.getattr(msg.guild.id, "prefixes")
    except AttributeError:
        # prefix handling runs before command checks, so there's a chance there's no guild
        custom_prefixes = ["s!"]
    except KeyError:
        # rare possibility, but you know
        custom_prefixes = []

    return mention_prefixes + custom_prefixes


def global_checks(ctx):
    if not ctx.bot.is_ready():
        return False

    if not ctx.guild:
        return False

    if not ctx.command:
        return True

    disable_entry = ctx.bot.config.getattr(ctx.guild.id, "disables")["users"].get(
        str(ctx.author.id)
    )
    if not disable_entry:
        return True

    if ctx.command.qualified_name in disable_entry:
        return False

    if "all" in disable_entry and not ctx.command.cog.qualified_name in (
        "Cog Control",
        "Eval",
        "Help",
    ):
        return False

    return True


async def on_init_load():
    await bot.wait_until_ready()

    bot.starboard = star_classes.StarboardEntries()
    bot.config = configs.GuildConfigManager()

    bot.star_queue = custom_classes.SetAsyncQueue()

    bot.snipes = {"deletes": {}, "edits": {}}
    bot.role_rolebacks = {}

    bot.image_extensions = tuple("jpg", "jpeg", "png", "gif", "webp")
    bot.added_db_info = False

    application = await bot.application_info()
    bot.owner = application.owner

    # is this overboard for a joke? yes.
    bot.death_messages = []
    mc_en_us_url = "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.16.5/assets/minecraft/lang/en_us.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(mc_en_us_url) as resp:
            mc_en_us_config = await resp.json(content_type="text/plain")

            for key, value in mc_en_us_config.items():
                if key.startswith("death.") and key not in (
                    "death.attack.message_too_long",
                    "death.attack.badRespawnPoint.link",
                ):
                    bot.death_messages.append(value)

    if not hasattr(bot, "pool"):

        async def add_json_converter(conn):
            await conn.set_type_codec(
                "jsonb",
                encoder=discord.utils.to_json,
                decoder=json.loads,
                schema="pg_catalog",
            )

        db_url = os.environ.get("DB_URL")
        bot.pool = await asyncpg.create_pool(
            db_url, min_size=2, max_size=5, init=add_json_converter
        )

    bot.load_extension("jishaku")
    bot.load_extension("cogs.db_handler")
    while not bot.added_db_info:
        await asyncio.sleep(0.1)

    cogs_list = utils.get_all_extensions(os.environ.get("DIRECTORY_OF_FILE"))

    for cog in cogs_list:
        if cog != "cogs.db_handler":
            try:
                bot.load_extension(cog)
            except commands.NoEntryPointError:
                pass

    await bot.slash.sync_all_commands()  # need to do this as otherwise slash cmds wont work


class SeraphimBot(commands.Bot):
    def __init__(
        self, command_prefix, help_command=bot_default, description=None, **options
    ):
        super().__init__(
            command_prefix,
            help_command=help_command,
            description=description,
            **options,
        )
        self._checks.append(global_checks)

    async def on_ready(self):
        utcnow = datetime.utcnow()
        time_format = utcnow.strftime("%x %X UTC")

        connect_msg = (
            f"Logged in at `{time_format}`!"
            if self.init_load == True
            else f"Reconnected at `{time_format}`!"
        )
        await self.owner.send(connect_msg)

        self.init_load = False

        activity = discord.Activity(
            name="over a couple of servers", type=discord.ActivityType.watching
        )

        try:
            await self.change_presence(activity=activity)
        except websockets.ConnectionClosedOK:
            await utils.msg_to_owner(self, "Reconnecting...")

    async def on_resumed(self):
        activity = discord.Activity(
            name="over a couple of servers", type=discord.ActivityType.watching
        )
        await self.change_presence(activity=activity)

    async def on_error(self, event, *args, **kwargs):
        try:
            raise
        except BaseException as e:
            await utils.error_handle(bot, e)

    async def get_context(self, message, *, cls=commands.Context):
        """A simple extension of get_content. If it doesn't manage to get a command, it changes the string used
        to get the command from - to _ and retries. Convenient for the end user."""

        ctx = await super().get_context(message, cls=cls)
        if ctx.command == None and ctx.invoked_with:
            ctx.command = self.all_commands.get(ctx.invoked_with.replace("-", "_"))

        return ctx

    async def close(self):
        try:
            await asyncio.wait_for(self.pool.close(), timeout=10)
        except asyncio.TimeoutError:
            await self.pool.terminate()

        return await super().close()


"""Suggesting the importance of which intents we use, let's break them down.
We need guilds as we need to know when the bot joins and leaves guilds for setup stuff. That's... mostly it.
We need members for their roles and nicknames. Yes, this stuff isn't provided normally.
Emojis are for the emoji helper commands, of course.
Messages run the entire core of the bot itself. Of course we use them here. We might be able to
turn off DM message intents, but for now they're here for safety.
Reactions run the starboard of Seraphim, so of course that's here too. See above for why DMs."""
intents = discord.Intents(
    guilds=True, members=True, emojis=True, messages=True, reactions=True
)

mentions = discord.AllowedMentions.all()

bot = SeraphimBot(
    command_prefix=seraphim_prefixes,
    chunk_guilds_at_startup=True,
    allowed_mentions=mentions,
    intents=intents,
)
slash = discord_slash.SlashCommand(bot, override_type=True)

try:
    import uvloop

    uvloop.install()
except ImportError:
    pass

bot.init_load = True

bot.loop.create_task(on_init_load())
bot.run(os.environ.get("MAIN_TOKEN"))
