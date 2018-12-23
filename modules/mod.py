import discord

from discord.ext import commands
from logger import get_logger
import loadconfig

__author__ = "NotThatSiri"
__version__ = "0.0.2"

logger = get_logger(__name__)


class mod():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden = True)
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    async def ban(self, ctx, member: discord.Member=None, *reason):
        '''ban a member with a reason (MOD ONLY)
        Example:
        -----------
        !dl ban @bob#1234
        '''
        if member is not None:
            if reason:
                reason = ' '.join(reason)
            else:
                reason = None
            await member.ban(reason=reason)
        else:
            await ctx.send('**:no_entry:** No Users found')

    @commands.command(hidden=True)
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    async def unban(self, ctx, user: int=None, *reason):
        '''unban a member with a reason (MOD ONLY)

        example:
        -----------
        !dl unban 102815825781596160
        '''
        user = discord.User(id=user)
        if user is not None:
            if reason:
                reason = ' '.join(reason)
            else:
                reason = None
            await ctx.guild.unban(user, reason=reason)
        else:
            await ctx.send('**:no_entry:** Kein Benutzer angegeben!')

    @commands.command(aliases=['prune'], hidden=True)
    @commands.has_permissions(manage_messages = True)
    @commands.bot_has_permissions(manage_messages = True)
    async def purge(self, ctx, *limit):
        '''delete amount of messages (MOD ONLY)
        Example:
        -----------
        !dl purge 100
        '''
        try:
            limit = int(limit[0])
        except IndexError:
            limit = 1
        deleted = 0
        while limit >= 1:
            cap = min(limit, 100)
            deleted += len(await ctx.channel.purge(limit=cap, before=ctx.message))
            limit -= cap
        tmp = await ctx.send(f'**:white_check_mark:** {deleted} Messages deleted')
        await asyncio.sleep(15)
        await tmp.delete()
        await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(kick_members = True)
    async def kick(self, ctx, member: discord.Member = None, *reason):
        '''Kick a member with a reason (MOD ONLY)
        example:
        -----------
        !dl kick @bob#1234
        '''
        if member is not None:
            if reason:
                reason = ' '.join(reason)
            else:
                reason = None
            await member.kick(reason=reason)
        else:
            await ctx.send('**:no_entry:** No user specified!')

def setup(bot):
    bot.add_cog(mod(bot))
