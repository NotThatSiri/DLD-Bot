import discord
from discord.ext import commands
import loadconfig
from logger import get_logger
logger = get_logger('discord')

description = '''DLD Bot For Dancing Line Discord'''
bot = commands.Bot(command_prefix=loadconfig.__prefix__, description=description)

@bot.event
async def on_ready():
    logger.info('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Dancing Line'))
    for cog in loadconfig.__cogs__:
        try:
            bot.load_extension(cog)
            logger.info('<{0}> Loaded successfully.'.format(cog))
        except Exception as e:
            logger.warning(f'Couldn\'t load cog {cog}')
            logger.error(e)
bot.run(loadconfig.__token__)
#bot.run(loadconfig.__tokentest__)
