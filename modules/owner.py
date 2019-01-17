import discord

from discord.ext import commands
from logger import get_logger

__author__ = "SpBonez"
__version__ = "0.0.1"

logger = get_logger(__name__)


class owner():
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.command(aliases=['quit'], hidden=True)
    async def shutdown(self, ctx):
        '''Stopping the bot :( (BOT OWNER ONLY)'''
        await ctx.send('**:ok:** Bye!')
        await self.bot.logout()
        sys.exit(0)

    @commands.command(hidden=True, aliases=['game'])
    async def changegame(self, ctx, gameType: str, *, gameName: str):
        '''Change the bots playing game (BOT OWNER ONLY)'''
        gameType = gameType.lower()
        if gameType == 'playing':
            type = discord.ActivityType.playing
        elif gameType == 'watching':
            type = discord.ActivityType.watching
        elif gameType == 'listening':
            type = discord.ActivityType.listening
        elif gameType == 'streaming':
            type = discord.ActivityType.streaming
        await self.bot.change_presence(activity=discord.Activity(type=type, name=gameName))

    @commands.command(hidden=True)
    async def changestatus(self, ctx, status: str):
        '''Change the  Online Status of the Bot (BOT OWNER ONLY)'''
        status = status.lower()
        if status == 'offline' or status == 'off' or status == 'invisible':
            discordStatus = discord.Status.invisible
        elif status == 'idle':
            discordStatus = discord.Status.idle
        elif status == 'dnd' or status == 'disturb':
            discordStatus = discord.Status.dnd
        else:
            discordStatus = discord.Status.online
        await self.bot.change_presence(status=discordStatus)

    @commands.command(hidden=True)
    async def name(self, ctx, name: str):
        '''Changes the global name of the Bot (BOT OWNER ONLY)'''
        await self.bot.edit_profile(username=name)

    @commands.command(hidden=True, aliases=['guilds'])
    async def servers(self, ctx):
        '''Lists the current servers the bot is in (BOT OWNER ONLY)'''
        msg = '```js\n'
        msg += '{!s:19s} | {!s:>5s} | {} | {}\n'.format('ID', 'Member', 'Name', 'Owner')
        for guild in self.bot.guilds:
            msg += '{!s:19s} | {!s:>5s}| {} | {}\n'.format(guild.id, guild.member_count, guild.name, guild.owner)
        msg += '```'
        await ctx.send(msg)

    @commands.command(hidden=True)
    async def leaveserver(self, ctx, guildid: str):
        '''get the bot to leave a server (BOT OWNER ONLY)
        syntax:
        -----------
        :leaveserver 102817255661772800
        '''
        guild = self.bot.get_guild(guildid)
        if guild:
            await self.bot.leave_guild(guild)
            msg = ':ok: bot has left {} successfully!'.format(guild.name)
        else:
            msg = ':x: could not find the server with that id'
        await ctx.send(msg)

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

def setup(bot):
    bot.add_cog(owner(bot))
