import asyncio
import discord
import random
import urllib
import requests
import json
import time
from   discord.ext import commands
from Cogs import Message
from Cogs import FuzzySearch
from Cogs import GetImage

# This module is for random funny things I guess...

class Humor:

	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		randnum = random.randint(0, len(fartList)-1)
		msg = '{}'.format(fartList[randnum])
		await self.bot.send_message(ctx.message.channel, msg)

	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await self.bot.send_message(channel, 'Too many images at once - please wait a few seconds.')
			return False

		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	@commands.command(pass_context=True)
	async def memetemps(self, ctx):
		"""Get Meme Templates"""
		url = "https://api.imgflip.com/get_memes"
		r = requests.get(url)
		result_json = json.loads(r.text)
		templates = result_json["data"]["memes"]

		templates_string_list = []

		templates_string = "**Meme Templates**\n"
		for template in templates:
			length_test = templates_string + "* [`{}` - `{}`]\n".format(template["id"], template["name"])
			if len(length_test) > 2000:
				# We're past our character limit - add it to the list and reset the
				# templates_string
				templates_string_list.append(templates_string)
				templates_string = ''
				continue
			# Not over the limit - add it to the string
			templates_string += "* [`{}` - `{}`]\n".format(template["id"], template["name"])
		# Add the templates_string to the list here if it contains anything
		if len(templates_string):
			templates_string_list.append(templates_string)
		# Iterate over all the template strings and display them
		for string in templates_string_list:
			await self.bot.send_message(ctx.message.author, string)

		# await Message.say(self.bot, templates_string, ctx.message.author)

	@commands.command(pass_context=True)
	async def meme(self, ctx, template_id = None, text_zero = None, text_one = None):
		"""Generate Meme"""

		if not self.canDisplay(ctx.message.server):
			return

		if text_one == None:
			# Set as space if not included
			text_one = " "

		if template_id == None or text_zero == None or text_one == None:
			msg = "Usage: `{}meme [template_id] [text#1] [text#2]`\n\n Meme Templates can be found using `$memetemps`".format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		templates = self.getTemps()

		chosenTemp = None
		msg = ''

		idMatch = FuzzySearch.search(template_id, templates, 'id', 1)
		if idMatch[0]['Ratio'] < 1:
			# Not a perfect match - try name
			nameMatch = FuzzySearch.search(template_id, templates, 'name', 1)
			if nameMatch[0]['Ratio'] > idMatch[0]['Ratio']:
				# Better match on name than id
				chosenTemp = nameMatch[0]['Item']['id']
				if not nameMatch[0]['Ratio'] == 1:
					# Still not a perfect match...
					msg = 'I\'ll assume you meant *{}*.'.format(nameMatch[0]['Item']['name'])
		else:
			# ID is a perfect match
			chosenTemp = idMatch[0]['Item']['id']


		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': chosenTemp, 'username':'1l11l1ll1l11', 'password': 'internet123', 'text0': text_zero, 'text1': text_one }
		r = requests.post(url, data=payload)
		result_json = json.loads(r.text)
		result = result_json["data"]["url"]
		if msg:
			# result = '{}\n{}'.format(msg, result)
			await self.bot.send_message(ctx.message.channel, msg)
		# Download Image - set title as a space so it disappears on upload
		await GetImage.get(result, self.bot, ctx.message.channel, " ")


	def getTemps(self):
		url = "https://api.imgflip.com/get_memes"
		r = requests.get(url)
		result_json = json.loads(r.text)
		templates = result_json["data"]["memes"]
		if templates:
			return templates
		return None
