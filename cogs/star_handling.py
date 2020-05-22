#!/usr/bin/env python3.7
from discord.ext import commands
import discord

import cogs.universals as univ
import cogs.star_universals as star_univ
import cogs.star_mes_handler as star_mes

class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            user, channel, mes = await univ.fetch_needed(self.bot, payload)
        except discord.HTTPException:
            univ.error_handle(self.bot, f"{payload.message_id}: could not find Message object. Channel: {payload.channel_id}", string=True)
            return

        if (str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id
            and not str(channel.id) in self.bot.star_config[mes.guild.id]["blacklist"].split(",")):

            star_variant = star_univ.get_star_entry(self.bot, mes.id, check_for_var=True)
            univ.error_handle(self.bot, str(star_variant), string=True)

            if star_variant == []:
                if channel.id != self.bot.star_config[mes.guild.id]["starboard_id"]:
                    star_univ.modify_stars(self.bot, mes, payload.user_id, "ADD")
                    unique_stars = star_univ.get_num_stars(star_variant)

                    if unique_stars >= self.bot.star_config[mes.guild.id]["star_limit"] and not self.bot.starboard[mes.id]["passed_star_limit"]:
                        star_mes.star_mes(self.bot, mes, unique_stars)
                            
            elif user.id != star_variant[0]["author_id"]:
                star_univ.modify_stars(self.bot, mes, payload.user_id, "ADD")
                star_univ.star_entry_refresh(self.bot, star_variant, mes.guild.id)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user, channel, mes = await univ.fetch_needed(self.bot, payload)

        if (str(payload.emoji) == "⭐" and not user.bot and mes.author.id != user.id
            and not str(channel.id) in self.bot.star_config[mes.guild.id]["blacklist"].split(",")):

            star_variant = star_univ.get_star_entry(self.bot, mes.id)

            if star_variant != []:
                star_univ.modify_stars(self.bot, mes, payload.user_id, "SUBTRACT")

                if star_variant["star_var_id"] != None:
                    star_univ.star_entry_refresh(self.bot, star_variant, mes.guild.id)
        
def setup(bot):
    bot.add_cog(Star(bot))