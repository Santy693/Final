import os
from dotenv import load_dotenv
from discord.ext import commands
import json
import urllib.request


load_dotenv()
token = os.getenv('discord_token')
bot = commands.Bot(command_prefix='!') #Prefijo del bot
