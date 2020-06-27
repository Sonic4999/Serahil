#!/usr/bin/env python3.7
from discord.ext import commands
import discord, importlib

import bot_utils.star_universals as star_univ
import bot_utils.universals as univ
import bot_utils.star_mes_handler as star_mes

class ModCMDs(commands.Cog, name = "Mod Star"):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(star_univ)
        importlib.reload(univ)
        importlib.reload(star_mes)

    @commands.group()
    @commands.check(univ.proper_permissions)
    async def star_settings(self, ctx):
        """The base for messing around with the starboard. Check the subcommands for more info.
        Requires Manage Server permissions or higher."""
        if ctx.invoked_subcommand == None:
            await ctx.send("Options: `channel`, `limit`, `toggle`")

    @star_settings.group()
    @commands.check(univ.proper_permissions)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Sets the starboard channel to the channel mentioned."""
        self.bot.config[ctx.guild.id]["starboard_id"] = channel.id
        await ctx.send(f"Set channel to {channel.mention}!")

    @star_settings.group()
    @commands.check(univ.proper_permissions)
    async def limit(self, ctx, limit):
        """Sets the amount of stars needed to get onto the starboard to that number."""
        if limit.isdigit():
            self.bot.config[ctx.guild.id]["star_limit"] = int(limit)
            await ctx.send(f"Set limit to {limit}!")
        else:
            await ctx.send("That doesn't seem like a valid number to me...")

    @star_settings.group()
    @commands.check(univ.proper_permissions)
    async def toggle(self, ctx):
        """Toggles the entirety of the starboard (including the commands, hopefully) on or off (defaults to off when it joins a new server).
        To toggle it, both the star channel and the star limit must be set beforehand."""

        guild_config = self.bot.config[ctx.guild.id]
        if guild_config["starboard_id"] != None and guild_config["star_limit"] != None:
            toggle = not guild_config["star_toggle"]
            self.bot.config[ctx.guild.id]["star_toggle"] = toggle
            await ctx.send(f"Toggled starboard to {toggle} for this server!")
        else:
            await ctx.send("Either you forgot to set the starboard channel or the star limit. Please try again.")

    @commands.command()
    @commands.check(univ.proper_permissions)
    async def force(self, ctx, mes_id):
        """Forces a message onto the starboard, regardless of how many stars it has.
        The message represented by the message id must be in the same channel as the channel you send the command.
        This message cannot be taken off the starboard unless it is deleted from it manually.
        You must have Manage Server permissions or higher to run this command."""
        
        if not self.bot.config[ctx.guild.id]["star_toggle"]:
            await ctx.send("Starboard is not turned on for this server!")
            return

        if not mes_id.isdigit():
            await ctx.send("Not a valid channel id!")
            return

        try:
            mes = await ctx.channel.fetch_message(int(mes_id))
        except discord.NotFound:
            await ctx.send("Message not found! Is this a valid message ID and are you running this command in the same channel as the message?")
            return

        star_univ.modify_stars(self.bot, mes, None, "None")
        starboard_entry = star_univ.get_star_entry(self.bot, mes.id)
        
        if starboard_entry["star_var_id"] == None:
            starboard_entry["forced"] == True
        else:
            await ctx.send("This message is already on the starboard!")
            return
        
        unique_stars = star_univ.get_num_stars(starboard_entry)
        await star_mes.send(self.bot, mes, unique_stars, forced=True)

        await ctx.send("Done!")

def setup(bot):
    bot.add_cog(ModCMDs(bot))