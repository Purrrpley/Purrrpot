import argparse
import asyncio
import importlib
import json
import os
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import discord


class Client(discord.Client):
  # Store commands as named tuple (so that the make_parser() function only 
  # has to be called once)
  Command = namedtuple('Command', ['command', 'parser'])
  
  # Custom errors
  class InvalidCommandError(Exception): pass
  class UnknownCommandError(Exception): pass
  
  @staticmethod
  def mention_to_text(mention: str):
    # Mentions in messages have a `!` in them, but `self.user.mention` and 
    # likely some other placed doesn't, so this function add it.
    return f'{mention[:2]}!{mention[2:]}'
  
  def __init__(self, executor: ThreadPoolExecutor, *args, **kwargs):
    self.executor = executor
    self.commands = {}
    
    # Load commands
    # TODO: Maybe move this to `self.load_command()` for use by `!load`?
    commands_to_load = []
    try:
      # Load commands from file
      with open('loaded_commands.json') as f:
        for command, enabled in json.load(f).items():
          if enabled:
            commands_to_load.append(command)
    except FileNotFoundError:
      # If the file doesn't exist, try and load all commands that don't begin 
      # with an underscore, and create the file.
      # TODO: Save file after loading commands (so that failed ones don't try 
      # to load next time)
      try:
        for file_path in os.listdir('commands'):
          if (
            not file_path.startswith('_')
            and os.path.isfile(os.path.join('commands', file_path))
            and os.path.splitext(file_path)[1] == '.py'
          ):
            commands_to_load.append(os.path.splitext(file_path)[0])
        with open('loaded_commands.json', 'w') as f:
          json.dump(
            {command: True for command in commands_to_load},
            f,
            indent=2
          )
        print(commands_to_load)
      except FileNotFoundError:
        print('No `commands` folder!')
    
    # Load the commands
    # TODO: Maybe move this somewhere else?
    failed_commands = self.load_commands(*commands_to_load)
    for failed_command, reason in failed_commands.items():
      if reason == ModuleNotFoundError:
        print(f'Cannot find module `{failed_command}.py`!')
      elif reason == AttributeError:
        print(
          f"Module `{failed_command}.py` doesn't implement the command API " 'properly!'
        )
      else:
        print(f'Failed to load `{failed_command}.py for an unknown reason!')
    
    # Check to see if "control commands" are loaded
    control_commands = ['load', 'unload', 'reload']
    for control_command in control_commands:
      if control_command not in self.commands:
        print(f'Warning: Command `{control_command}` not loaded!')
    
    # Don't override `discord.Client.__init__()`
    super().__init__(*args, **kwargs)
  
  async def on_ready(self):
    print('Ready!')
  
  async def on_connect(self):
    print('Connected!')
  
  async def on_disconnect(self):
    print('Disconnected!')
  
  async def on_resumed(self):
    print('Resumed!')
  
  async def on_message(self, message: discord.Message):
    # Never reply to self
    if message.author.id == self.user.id:
      return
    
    # Only reply to commands. Commands are either prefixed with the prefix 
    # charater, or prefixed with a mention to the bot.
    if not (
      message.content.startswith('!')
      or message.content.startswith(self.mention_to_text(self.user.mention))
    ):
      return
    
    # Log
    print(f'{message.author}: {message.content}')
    
    # Parse the message
    try:
      commands = self.parse_command(message.content)
    except self.InvalidCommandError:
      print(f'Invalid command: {message.content}')
      return
    
    # Run the command(s)
    for command, args in commands.items():
      if command in self.commands.keys():
        await self.run_command(
          command,
          message,
          self.commands[command].parser.parse_args(args),
        )
      else:
        print(f'Command not found: {command} ({args})')
    
    return
  
  def parse_command(self, text: str) -> dict:
    # Remove command prefix and subsequent proceeding white-space from message
    if text.startswith('!'):
      stripped_text = text.removeprefix('!')
    else:
      stripped_text = text.removeprefix(
        self.mention_to_text(self.user.mention)
      )
    stripped_text = stripped_text.lstrip()
    
    # TODO: This should consider several things before returning a list of 
    # arguments. It should consider quotes and deal with them like shells do 
    # (or at least how bash does), and allow multiple commands to be executes 
    # at once with `&&` and `||` syntax, also like shells. Additionally, it 
    # should be able to work well with multiple lines. 
    
    split_text = stripped_text.split()
    
    # Raise `self.InvalidCommandError` if the command given was just a prefix. 
    # This error should also be raised if something else about the text was 
    # invalid when parsing it (such as invalid use of quotes).
    if len(split_text) >= 1:
      return {split_text[0]: split_text[1:]}
    else:
      raise self.InvalidCommandError
  
  async def run_command(
    self,
    command: str,
    message: discord.Message,
    args: argparse.Namespace,
  ):
    # Run a command, and if the command function returns something other than 
    # None, send it as a message (which is a useful shorthand for simple 
    # commands).
    result = await self.loop.run_in_executor(
      self.executor,  # Executor to run the command in
      self.commands[command].command,  # The function to run
      self, message, args,  # The args to pass to the function
    )
    if result != None:
      await message.channel.send(result)
  
  def run_coro(self, coro):
    asyncio.run_coroutine_threadsafe(coro, self.loop)
  
  def load_commands(self, *commands: str) -> dict:
    # Unloading then loading a module is not the same as reloading it!
    importlib.invalidate_caches()
    
    invalid_commands = {}
    for command in commands:
      # Try to import the module
      try:
        imported_command = importlib.import_module(f'commands.{command}')
      except ModuleNotFoundError:
        invalid_commands[command] = ModuleNotFoundError
        continue
      
      # Check to see if the module implements the command API
      try:
        for function_name in ['command', 'make_parser']:
          if not callable(getattr(imported_command, function_name)):
            raise AttributeError
      except AttributeError:
        invalid_commands[command] = AttributeError
        continue
      # Add the command
      self.commands[command] = self.Command(
        imported_command.command,
        imported_command.make_parser(),
      )
    
    return invalid_commands
  
  def unload_commands(self, *commands: str) -> dict:
    # Can't actually *unload* functions, but can unbind them. To reload them, 
    # the reload_commands() function has to be used.
    invalid_commands = {}
    for command in commands:
      try:
        self.commands.pop(command)
      except KeyError:
        invalid_commands[command] = KeyError
    
    return invalid_commands
  
  def reload_commands(self, *commands: str) -> dict:
    # Doesn't truly reload, but should be close enough for most cases.
    # https://docs.python.org/3/library/importlib.html#importlib.reload
    invalid_commands = {}
    for command in commands:
      try:
        importlib.reload(self.commands[command])
      except ModuleNotFoundError:
        invalid_commands[command] = ModuleNotFoundError
    
    return invalid_commands


if __name__ == '__main__':
  # Get token
  with open('access_token.txt') as f:
    TOKEN = f.read()
  
  # Run bot
  with ThreadPoolExecutor() as e:
    client = Client(e)
    client.run(TOKEN)
