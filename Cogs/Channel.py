import asyncio
import discord
import time
import os
from   discord.ext import commands
from   datetime import datetime
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Channel:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.cleanChannels = []
		
		
	async def member_update(self, before, after):
		server = after.server

		# Check if the member went offline and log the time
		if str(after.status).lower() == "offline":
			currentTime = int(time.time())
			self.settings.setUserStat(after, server, "LastOnline", currentTime)

		self.settings.checkServer(server)
		try:
			channelMOTDList = self.settings.getServerStat(server, "ChannelMOTD")
		except KeyError:
			channelMOTDList = []

		if len(channelMOTDList) > 0:
			members = 0
			membersOnline = 0
			for member in server.members:
				members += 1
				if str(member.status).lower() == "online":
					membersOnline += 1

		for id in channelMOTDList:
			channel = self.bot.get_channel(id['ID'])
			if channel:
				motd = id['MOTD'] # A markdown message of the day
				listOnline = id['ListOnline'] # Yes/No - do we list all online members or not?	
				if listOnline.lower() == "yes":
					msg = '{} - ({}/{} users online)'.format(motd, int(membersOnline), int(members))
				else:
					msg = motd
				try:
					await self.bot.edit_channel(channel, topic=msg)
				except Exception:
					continue
					
		
	@commands.command(pass_context=True)
	async def islocked(self, ctx):
		"""Says whether the bot only responds to admins."""
		
		isLocked = self.settings.getServerStat(ctx.message.server, "AdminLock")
		if isLocked.lower() == "yes":
			msg = 'Admin lock is *On*.'
		else:
			msg = 'Admin lock is *Off*.'
			
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.message.server, "Rules")
		msg = "*{}* Rules:\n{}".format(ctx.message.server.name, rules)
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def ismuted(self, ctx, *, member = None):
		"""Says whether a member is muted in chat."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
			
		if member == None:
			msg = 'Usage: `{}ismuted [member]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.server)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		mutedIn = 0
		channelList = []
		for channel in ctx.message.server.channels:
			if not channel.type is discord.ChannelType.text:
				continue
			overs = channel.overwrites_for(member)
			if overs.send_messages == False:
				# We haven't been muted here yet
				overs.send_messages = False
				await self.bot.edit_channel_permissions(channel, member, overs)
				perms = member.permissions_in(channel)
				if perms.read_messages:
					mutedIn +=1
					channelList.append(channel.name)
				
		if len(channelList):
			# Get time remaining if needed
			cd = self.settings.getUserStat(member, ctx.message.server, "Cooldown")
			if not cd == None:
				ct = int(time.time())
				checkRead = ReadableTime.getReadableTimeBetween(ct, cd)
				msg = '*{}* is **muted** in *{}*\n*{}* remain'.format(DisplayName.name(member), ', '.join(channelList), checkRead)
			else:
				msg = '*{}* is **muted** in *{}*.'.format(DisplayName.name(member), ', '.join(channelList))	
		else:
			msg = '{} is **unmuted**.'.format(DisplayName.name(member))
			
		await self.bot.send_message(ctx.message.channel, msg)
		
	@ismuted.error
	async def ismuted_error(self, ctx, error):
		# do stuff
		msg = 'ismuted Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def listadmin(self, ctx):
		"""Lists admin roles and id's."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		promoArray = self.settings.getServerStat(ctx.message.server, "AdminArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no admin roles set yet.  Use `{}addadmin [role]` to add some.".format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, roleText)
			return
		
		roleText = "Current Admin Roles:\n"

		for arole in promoSorted:
			found = False
			for role in ctx.message.server.roles:
				if role.id == arole["ID"]:
					# Found the role ID
					found = True
					roleText = '{}**{}** (ID : `{}`)\n'.format(roleText, role.name, arole['ID'])
			if not found:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, arole['Name'])

		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await self.bot.send_message(ctx.message.channel, roleText)

	@commands.command(pass_context=True)
	async def rolecall(self, ctx, *, role = None):
		"""Lists the number of users in a current role."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		if role == None:
			msg = 'Usage: `{}rolecall [role]`'.format(ctx.prefix)
			await self.bot.send_message(channel, msg)
			return
			
		if type(role) is str:
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.server)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return
		
		# Create blank embed
		role_embed = discord.Embed(color=role.color)
		# Get server's icon url if one exists - otherwise grab the default blank Discord avatar
		avURL = server.icon_url
		if not len(avURL):
			avURL = discord.User.default_avatar_url
		# Add the server icon
		# role_embed.set_author(name='{}'.format(role.name), icon_url=avURL)
		role_embed.set_author(name='{}'.format(role.name))

		# We have a role
		memberCount = 0
		memberOnline = 0
		for member in server.members:
			roles = member.roles
			if role in roles:
				# We found it
				memberCount += 1
				if str(member.status).lower() == 'online':
					memberOnline+= 1

		'''if memberCount == 1:
			msg = 'There is currently *1 user* with the **{}** role.'.format(role.name)
			role_embed.add_field(name="Members", value='1 user', inline=True)
		else:
			msg = 'There are currently *{} users* with the **{}** role.'.format(memberCount, role.name)
			role_embed.add_field(name="Members", value='{}'.format(memberCount), inline=True)'''
		
		role_embed.add_field(name="Members", value='{} out of {} online.'.format(memberOnline, memberCount), inline=True)
			
		# await self.bot.send_message(channel, msg)
		await self.bot.send_message(channel, embed=role_embed)


	@rolecall.error
	async def rolecall_error(self, ctx, error):
		# do stuff
		msg = 'rolecall Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def log(self, ctx, messages : int = 25, *, chan : discord.Channel = None):
		"""Logs the passed number of messages from the given channel - 25 by default (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		# Check for admin status
		isAdmin = author.permissions_in(channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(server, "AdminArray")
			for role in author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True

		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		logFile = 'Logs-{}.txt'.format(timeStamp)

		if not chan:
			chan = channel

		# Remove original message
		await self.bot.delete_message(ctx.message)

		mess = await self.bot.send_message(ctx.message.author, 'Saving logs to *{}*...'.format(logFile))

		# Use logs_from instead of purge
		counter = 0
		msg = ''
		async for message in self.bot.logs_from(channel, limit=messages):
			counter += 1
			msg += message.content + "\n"
			msg += '----Sent-By: ' + message.author.name + '#' + message.author.discriminator + "\n"
			msg += '---------At: ' + message.timestamp.strftime("%Y-%m-%d %H.%M") + "\n"
			if message.edited_timestamp:
				msg += '--Edited-At: ' + message.edited_timestamp.strftime("%Y-%m-%d %H.%M") + "\n"
			msg += '\n'

		msg = msg[:-2].encode("utf-8")

		with open(logFile, "wb") as myfile:
			myfile.write(msg)

		
		message = await self.bot.edit_message(mess, 'Uploading *{}*...'.format(logFile))
		await self.bot.send_file(ctx.message.author, logFile)
		message = await self.bot.edit_message(mess, 'Uploaded *{}!*'.format(logFile))
		os.remove(logFile)

		

	@commands.command(pass_context=True)
	async def clean(self, ctx, messages : int = 100, *, chan : discord.Channel = None):
		"""Cleans the passed number of messages from the given channel - 100 by default, 1000 max (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		# Check for admin status
		isAdmin = author.permissions_in(channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(server, "AdminArray")
			for role in author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True

		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if not chan:
			chan = channel

		if chan in self.cleanChannels:
			# Don't clean messages from a channel that's being cleaned
			return

		# Remove original message
		await self.bot.delete_message(ctx.message)

		if messages > 1000:
			messages = 1000

		# Use logs_from instead of purge
		counter = 0

		# Add channel to list
		self.cleanChannels.append(ctx.message.channel)
		# I tried bulk deleting - but it doesn't work on messages over 14 days
		# old - so we're doing them individually I guess.
		totalMess = messages
		while totalMess > 0:
			gotMessage = False
			if totalMess > 100:
				tempNum = 100
			else:
				tempNum = totalMess
			try:
				async for message in self.bot.logs_from(channel, limit=tempNum):
					await self.bot.delete_message(message)
					gotMessage = True
					counter += 1
					totalMess -= 1
			except Exception:
				pass
			if not gotMessage:
				# No more messages - exit
				break

		# Remove channel from list
		self.cleanChannels.remove(ctx.message.channel)

		# Send the cleaner a pm letting them know we're done
		if counter == 1:
			await self.bot.send_message(ctx.message.author, '*1* message removed from *#{}* in *{}!*'.format(channel.name, server.name))
		else:
			await self.bot.send_message(ctx.message.author, '*{}* messages removed from *#{}* in *{}!*'.format(counter, channel.name, server.name))

		# Remove the rest
		# await self.bot.purge_from(chan, limit=messages)
