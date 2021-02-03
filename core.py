import argparse
import asyncio
import importlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import discord


def quantum_vortex(client, message):
	send_message(
		client,
		message.channel,
		f'Assembling quantum vortex #{message.content}...'
	)
	time.sleep(1)
	send_message(
		client,
		message.channel,
		f'Quantum vortex #{message.content} assembled!'
	)


# Wrapper for `messageable.send()`, allowing it to easily be called from 
# synchronous functions. Reading for why it's done this way:
# https://docs.python.org/3/library/asyncio-dev.html#asyncio-multithreading
# ---
# Probably should be changed to be a Client method
def send_message(
		client: discord.Client,
		messageable: discord.abc.Messageable,
		*args,
		**kwargs,
	):
	asyncio.run_coroutine_threadsafe(
		messageable.send(*args, **kwargs),
		client.loop,
	)


class Client(discord.Client):
	# Add the command executor argument without overriding discord.Client's 
	# __init__ method
	def __init__(self, executor: ThreadPoolExecutor, *args, **kwargs):
		self.executor = executor
		self.commands = {}
		self.load_commands('hi')
		super().__init__(*args, **kwargs)
	
	async def on_ready(self):
		print('Ready!')
	
	async def on_disconnect(self):
		print('Disconnected!')
	
	async def on_message(self, message: discord.Message):
		# Never reply to self
		if message.author.id == self.user.id:
			return
		
		# Only reply to commands. Commands are either prefixed with the prefix 
		# charater, or prefixed with a mention to the bot. Mentions in 
		# messages have a "!" in them, and `self.user.mention` doesn't, so 
		# that needs to be added manually. 
		user_mention_text = '{}!{}'.format(
			self.user.mention[:2],
			self.user.mention[2:],
		)
		if not (
			message.content.startswith('!')
			or message.content.startswith(user_mention_text)
		):
			return
		
		# Remove command specifier from message (and proceeding white-space)
		if message.content.startswith('!'):
			stripped_message = message.content.removeprefix('!')
		else:
			stripped_message = message.content.removeprefix(user_mention_text)
		stripped_message = stripped_message.lstrip()
		
		
		# TODO: Turn message string into argument list (perhaps with 
		# `str.split()`), and then execute the command.
		# 
		# How the command API should work:
		# * Commands are put in the `modules` folder as Python modules
		# * All modules in the `modules` folder are loaded/reloaded on command 
		# without requiring a bot restart
		# * Command modules should include 2 commands:
		#   1: command(client, message, namespace)
		#   2: arg_parser()
		# command() function is executed, arg_parser() function should return 
		# an argparser.ArgumentParser object that is used to parse the 
		# arguments for the command.
		# 
		# Command modules should be able to use `send_message()` from this 
		# file. `__init__.py` might be useful here?
		
		
		msg = stripped_message.split()
		
		if msg[0] == 'hi':
			print(self.reload_commands('hi'))
			self.commands['hi'].command(
				self,
				message,
				self.commands['hi'].arg_parser().parse_args(msg[1:]),
			)
		
		
		# # Run command
		# await self.loop.run_in_executor(
		# 	self.executor,
		# 	quantum_vortex,  # Func
		# 	self,  # arg1
		# 	message,  # arg2
		# )
		
		# Log
		print(f'{message.author}: {stripped_message}')
	
	def run_coro(self, coro):
		asyncio.run_coroutine_threadsafe(coro, self.loop)
	
	def load_commands(self, *commands: str) -> dict:
		importlib.invalidate_caches()
		
		invalid_commands = {}
		for command in commands:
			try:
				# Import module
				self.commands[command] = importlib.import_module(
					f'commands.{command}'
				)
			except ModuleNotFoundError:
				invalid_commands[command] = ModuleNotFoundError
				continue
			try:
				# Check to see if the module implements the command API
				for function_name in ['command', 'arg_parser']:
					if not callable(getattr(
						self.commands[command],
						function_name,
					)):
						raise AttributeError
			except AttributeError:
				invalid_commands[command] = AttributeError
		
		return invalid_commands
	
	def unload_commands(self, *commands: str):
		importlib.invalidate_caches()
		
		
		invalid_commands = {}
		
		for command in commands:
			try:
				self.commands.pop(command)
			except KeyError:
				invalid_commands[command] = KeyError
		
		return invalid_commands
	
	def reload_commands(self, *commands: str):
		invalid_commands = {}
		
		for command in commands:
			try:
				importlib.reload(self.commands[command])
			except ModuleNotFoundError:
				invalid_commands[command] = ModuleNotFoundError
		
		return invalid_commands
		
		
		# invalid_unload = self.unload_commands(*commands)
		# invalid_load = self.load_commands(*commands)
		
		# return invalid_unload, invalid_load


if __name__ == '__main__':
	# Get token
	with open('access_token.txt') as f:
		TOKEN = f.read()

	# Run bot
	with ThreadPoolExecutor() as e:
		client = Client(e)
		client.run(TOKEN)
