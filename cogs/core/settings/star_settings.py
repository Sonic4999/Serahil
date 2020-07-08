from discord.ext import commands
import discord, typing

import common.utils as utils

@commands.group(name="starboard", aliases=["sb"])
@commands.check(utils.proper_permissions)
async def main_cmd(ctx):
    """The base for messing around with the starboard. Check the subcommands for more info.
    Requires Manage Server permissions or higher."""
    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def channel(ctx, channel: typing.Optional[discord.TextChannel]):
    """Allows you to either get the starboard channel (no argument) or set the starboard channel (with argument)."""

    if channel != None:
        ctx.bot.config[ctx.guild.id]["starboard_id"] = channel.id
        await ctx.send(f"Set channel to {channel.mention}!")
    else:
        starboard_id = ctx.bot.config[ctx.guild.id]['starboard_id']
        starboard_mention = f"<#{starboard_id}>" if starboard_id != None else "None"
        await ctx.send(f"Starboard channel: {starboard_mention}")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def limit(ctx, limit: typing.Optional[int]):
    """Allows you to either get the amount of stars needed to get on the starboard (no argument) or set the amount (with argument)."""
    if limit != None:
        if limit.isdigit():
            ctx.bot.config[ctx.guild.id]["star_limit"] = int(limit)
            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a valid number to me...")
    else:
        await ctx.send(f"Star limit: {ctx.bot.config[ctx.guild.id]['star_limit']}")

@main_cmd.command()
@commands.check(utils.proper_permissions)
async def toggle(ctx, toggle: typing.Optional[bool]):
    """Allows you to either see if all starboard-related commands and actions are on or off (no argument) or allows you to toggle that (with argument).
    If you wish to set the toggle, both the starboard channel and the star limit must be set first."""

    if toggle != None:
        guild_config = ctx.bot.config[ctx.guild.id]
        if guild_config["starboard_id"] != None and guild_config["star_limit"] != None:
            ctx.bot.config[ctx.guild.id]["star_toggle"] = toggle
            await ctx.send(f"Toggled starboard to {toggle} for this server!")
        else:
            await ctx.send("Either you forgot to set the starboard channel or the star limit. Please try again.")
    else:
        await ctx.send(f"Star toggle: {ctx.bot.config[ctx.guild.id]['star_toggle']}")


def star_toggle_check(ctx):
    return ctx.bot.config[ctx.guild.id]["star_toggle"]

@main_cmd.group(aliases = ["bl"])
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def blacklist(ctx):
    """The base command for the star blacklist. See the subcommands for more info.
    Requires Manage Server permissions or higher."""

    if ctx.invoked_subcommand == None:
        await ctx.send_help(ctx.command)

@blacklist.command(name = "list")
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def _list(ctx):
    """Returns a list of channels that have been blacklisted. Messages from channels that are blacklisted won’t be starred."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]
    if channel_id_list != []:
        channel_mentions = []

        for channel_id in channel_id_list:
            channel = await ctx.bot.get_channel(channel_id)

            if channel != None:
                channel_mentions.append(channel.mention)
            else:
                del ctx.bot.config[ctx.guild.id]["star_blacklist"][channel_id]

        if channel_mentions != []:
            await ctx.send(f"Blacklisted channels: {', '.join(channel_mentions)}")
            return
            
    await ctx.send("There's no blacklisted channels for this guild!")

@blacklist.command()
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def add(ctx, channel: discord.TextChannel):
    """Adds the channel to the blacklist."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]

    if not channel.id in channel_id_list:
        channel_id_list.append(channel.id)
        ctx.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
        await ctx.send(f"Addded {channel.mention} to the blacklist!")
    else:
        await ctx.send("That channel's already in the blacklist!")

@blacklist.command()
@commands.check(utils.proper_permissions)
@commands.check(star_toggle_check)
async def remove(ctx, channel: discord.TextChannel):
    """Removes the channel from the blacklist."""

    channel_id_list = ctx.bot.config[ctx.guild.id]["star_blacklist"]

    if channel.id in channel_id_list:
        channel_id_list.remove(channel.id)
        ctx.bot.config[ctx.guild.id]["blacklist"] = channel_id_list
        await ctx.send(f"Removed {channel.mention} from the blacklist!")
    else:
        await ctx.send("That channel's not in the blacklist!")