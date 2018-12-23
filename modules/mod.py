import discord

from discord.ext import commands
from logger import get_logger
import loadconfig

__author__ = "NotThatSiri"
__version__ = "0.0.1"

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
        :ban @bob#1234
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
        :unban 102815825781596160
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

def setup(bot):
    bot.add_cog(mod(bot))
