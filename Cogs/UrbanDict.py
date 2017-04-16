import asyncio
import discord
import requests
import string
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import Message
from   Cogs import Nullify

# This module grabs Urban Dictionary definitions

class UrbanDict:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.ua = 'CorpNewt DeepThoughtBot'

	@commands.command(pass_context=True)
	async def define(self, ctx, *, word : str):
		"""Gives the definition of the word passed."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		if not word:
			msg = 'Usage: `{}define [word]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return
		rword = word.replace(" ", "+")
		url = "http://api.urbandictionary.com/v0/define?term={}".format(rword)
		msg = 'I couldn\'t find a definition for "{}"...'.format(word) 
		r = requests.get(url, headers = {'User-agent': self.ua})
		theJSON = r.json()["list"]
		if len(theJSON):
			# Got it - let's build our response
			ourWord = theJSON[0]
			msg = '__**{}:**__\n\n{}'.format(string.capwords(ourWord["word"]), ourWord["definition"])
			if ourWord["example"]:
				msg = '{}\n\n__Example(s):__\n\n*{}*'.format(msg, ourWord["example"])
		
		# await self.bot.send_message(ctx.message.channel, msg)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await Message.say(self.bot, msg, ctx.message.channel)

	@commands.command(pass_context=True)
	async def randefine(self, ctx):
		"""Gives a random word and its definition."""
		url = "http://api.urbandictionary.com/v0/random"
		r = requests.get(url, headers = {'User-agent': self.ua})
		theJSON = r.json()["list"]
		if len(theJSON):
			# Got it - let's build our response
			ourWord = theJSON[0]
			msg = '__**{}:**__\n\n{}'.format(string.capwords(ourWord["word"]), ourWord["definition"])
			if ourWord["example"]:
				msg = '{}\n\n__Example(s):__\n\n*{}*'.format(msg, ourWord["example"])
		
		# await self.bot.send_message(ctx.message.channel, msg)
		await Message.say(self.bot, msg, ctx.message.channel)
