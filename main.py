#!/usr/bin/env python3.7
import discord, os, asyncio
from discord.ext import commands

import logging, time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename=os.environ.get("LOG_FILE_PATH"), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler.formatter.converter = time.gmtime
logger.addHandler(handler)

async def _prefix(bot, msg):
    bot_id = bot.user.id
    return [f"<@{bot_id}> ", f"<@!{bot_id}> ", "s!"]

bot = commands.Bot(command_prefix=_prefix, fetch_offline_members=True)

bot.remove_command("help")

@bot.event
async def on_ready():

    if bot.init_load == True:
        bot.starboard = {}
        bot.star_config = {}
        bot.logger = logger
        bot.load_extension("cogs.db_handler")
        while bot.star_config == {}:
            await asyncio.sleep(0.1)

        cogs_list = ["cogs.events.on_errors", "cogs.events.star_handling", "cogs.events.clear_events", "cogs.cmds.norm_cmds",
        "cogs.cmds.admin_cmds", "cogs.cmds.blacklist_cmds", "cogs.cmds.owner_cmds"]

        for cog in cogs_list:
            bot.load_extension(cog)

        bot.init_load = False

    utcnow = datetime.utcnow()
    time_format = utcnow.strftime("%x %X UTC")

    application = await bot.application_info()
    owner = application.owner

    connect_msg = f"Logged in at `{time_format}`!" if bot.on_readies == 0 else f"Reconnected at `{time_format}`!"

    await owner.send(connect_msg)
    activity = discord.Activity(name = 'for stars!', type = discord.ActivityType.watching)
    await bot.change_presence(activity = activity)
        
@bot.check
async def block_dms(ctx):
    return ctx.guild is not None

bot.init_load = True
bot.run(os.environ.get("MAIN_TOKEN"))