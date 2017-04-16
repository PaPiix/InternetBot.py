import asyncio
import discord
import os
import time
from   datetime import datetime
from   discord.ext import commands

# This is the RateLimit module. It keeps users from being able to spam commands

class RateLimit:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.commandCooldown = 5 # 5 seconds between commands - placeholder, overridden by settings
		self.maxCooldown = 10 # 10 seconds MAX between commands for cooldown
		
	def canRun( self, firstTime, threshold ):
		# Check if enough time has passed since the last command to run another
		currentTime = int(time.time())
		if currentTime > (int(firstTime) + int(threshold)):
			return True
		else:
			return False

	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages - but may need to ignore
		ignore = False

		# Get current delay
		try:
			currDelay = self.settings.serverDict['CommandCooldown']
		except KeyError:
			currDelay = self.commandCooldown
		
		# Check if we can run commands
		lastTime = int(self.settings.getUserStat(message.author, message.server, "LastCommand"))
		if not self.canRun( lastTime, currDelay ):
			# We can't run commands yet - ignore
			ignore = True
		
		return { 'Ignore' : ignore, 'Delete' : False }
		
	async def oncommand(self, command, ctx):
		# Let's grab the user who had a completed command - and set the timestamp
		self.settings.setUserStat(ctx.message.author, ctx.message.server, "LastCommand", int(time.time()))


	@commands.command(pass_context=True)
	async def ccooldown(self, ctx, delay : int = None):
		"""Sets the cooldown in seconds between each command (owner only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Only allow owner to change server stats
		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
				await self.bot.send_message(channel, msg)
				return

		# Get current delay
		try:
			currDelay = serverDict['CommandCooldown']
		except KeyError:
			currDelay = self.commandCooldown
		
		if delay == None:
			if currDelay == 1:
				await self.bot.send_message(ctx.message.channel, 'Current command cooldown is *1 second.*')
			else:
				await self.bot.send_message(ctx.message.channel, 'Current command cooldown is *{} seconds.*'.format(currDelay))
			return
		
		try:
			delay = int(delay)
		except Exception:
			await self.bot.send_message(ctx.message.channel, 'Cooldown must be an int.')
			return
		
		if delay < 0:
			await self.bot.send_message(ctx.message.channel, 'Cooldown must be at least *0 seconds*.')
			return

		if delay > self.maxCooldown:
			if self.maxCooldown == 1:
				await self.bot.send_message(ctx.message.channel, 'Cooldown cannot be more than *1 second*.')
			else:
				await self.bot.send_message(ctx.message.channel, 'Cooldown cannot be more than *{} seconds*.'.format(self.maxCooldown))
			return
		
		serverDict['CommandCooldown'] = delay
		if delay == 1:
			await self.bot.send_message(ctx.message.channel, 'Current command cooldown is now *1 second.*')
		else:
			await self.bot.send_message(ctx.message.channel, 'Current command cooldown is now *{} seconds.*'.format(delay))