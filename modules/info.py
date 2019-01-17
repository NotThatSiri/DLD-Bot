import discord
import asyncio
from discord.ext import commands
from logger import get_logger
import loadconfig
from wikia import wikia

__author__ = "NotThatSiri"
__version__ = "0.0.1"

logger = get_logger(__name__)

class info():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx, *arg1):
        member = ctx.author
        arg1 = ' '.join(arg1)
        searchword = arg1.title()
        mb = wikia.page("dancingline", str(searchword))
        embed = discord.Embed(title=mb.title, description=mb.content,url=mb.url, colour=member.colour)
        embed.set_author(icon_url=member.avatar_url, name=str(member))
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        if mb.images == []:
            pass
        else:
            embed.set_image(url=mb.images[0])

        await ctx.send(content=None, embed=embed)
        #await ctx.send(mb.images)
        #await ctx.send()

def setup(bot):
    bot.add_cog(info(bot))
