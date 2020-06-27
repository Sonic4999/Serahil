#!/usr/bin/env python3.7
from discord.ext import commands
import discord, datetime

class SnipeCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def snipe(self, ctx):
        """Allows you to get the last deleted message from the channel this command was used in."""

        no_msg_found = False

        if not ctx.channel.id in self.bot.sniped.keys():
            no_msg_found = True
        else:
            now = datetime.datetime.utcnow()
            one_minute = datetime.timedelta(minutes=1)
            one_minute_ago = now - one_minute

            if self.bot.sniped[ctx.channel.id]["time_deleted"] < one_minute_ago:
                no_msg_found = True
                del self.bot.sniped[ctx.channel.id]

        if no_msg_found:
            await ctx.send("There's nothing to snipe!")
            return

        sniped_msg = self.bot.sniped[ctx.channel.id]

        author = f"{sniped_msg['author'].display_name} ({str(sniped_msg['author'])})"
        icon = str(sniped_msg['author'].avatar_url_as(format="jpg", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=author, icon_url=icon)

        await ctx.send(embed = send_embed)

    @commands.command()
    async def editsnipe(self, ctx):
        """Allows you to get the last edited message from the channel this command was used in."""

        no_msg_found = False

        if not ctx.channel.id in self.bot.editsniped.keys():
            no_msg_found = True
        else:
            now = datetime.datetime.utcnow()
            one_minute = datetime.timedelta(minutes=1)
            one_minute_ago = now - one_minute

            if self.bot.editsniped[ctx.channel.id]["time_edited"] < one_minute_ago:
                no_msg_found = True
                del self.bot.editsniped[ctx.channel.id]

        if no_msg_found:
            await ctx.send("There's nothing to snipe!")
            return

        sniped_msg = self.bot.editsniped[ctx.channel.id]

        author = f"{sniped_msg['author'].display_name} ({str(sniped_msg['author'])})"
        icon = str(sniped_msg['author'].avatar_url_as(format="jpg", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0x4378fc), description=sniped_msg["content"], timestamp=sniped_msg["created_at"])
        send_embed.set_author(name=author, icon_url=icon)

        await ctx.send(embed = send_embed)

def setup(bot):
    bot.add_cog(SnipeCMDs(bot))