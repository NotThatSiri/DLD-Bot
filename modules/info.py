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
        arg1 = ' '.join(arg1)
        searchword = arg1.title()
        mb = wikia.page("dancingline", str(searchword))
        await ctx.send(mb.url)

def setup(bot):
    bot.add_cog(info(bot))
