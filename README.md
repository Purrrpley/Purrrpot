# What is Purrrpot?

Purrrpot is a [Discord](https://discord.com/) bot that allows for the writing  of extensions that can be loaded and reloaded without requiring a restart, and can be run asynchronously without async/await syntax. An extension's command can be executed with shell-like syntax. This is custom extensions API built on-top of [discord.py](https://github.com/Rapptz/discord.py).

# Core and Extensions

Purrrpot is made of 2 parts... The core (`core.py`), and the extensions (`extensions/*.py`). The core handles the bot's connection to Discord, as well as several other important central things. The extensions contain the code for all commands and schedules, and allow the bot to actually do useful things.

# Extensions API

Extensions should define a command and an argument parser for that command, and/or define a schedule and something to run on that schedule. For example:

```py
import argparse
import time


def make_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('text', type=str)
  parser.add_argument('--delay', '-d', type=int)
  parser.add_argument('--remember', '-r', action='store_true', default=False)
  return parser


def command(client, msg, args):
  if args.delay:
    text = (
      f'Hello after {args.delay} seconds! I was called by {msg.author.name}'
    )
    _say_after_delay(client, msg.channel, text, args.delay, args.remember)
  else:
    return f"Hello {msg.author.name}! Here's some text: \"{args.text}\""


def _say_after_delay(client, location, text, delay, remember=False):
  if remember:
    client.schedule(delay, 0, client.run_coro, location.send(text))
  else:
    time.sleep(args.delay)
    location.send(text)


def get_cron_schedule():
  return '@hourly'


def scheduled(client):
  for guild in client.guilds:
    for channel in channels:
      if (
        channel.name == 'hourly-text'
        and channel.permissions_for(client.user).send_messages
      ):
        client.run_coro(channel.send("Here's your hourly text!"))
```

# Class Extensions API

The API should likely be a class instead, for several reasons. An example of how this could work:

```py
import argparse
import time


class Extension:
  def __init__(self, client):
    self.client = client
    
    self.parser = argparse.ArgumentParser()
    self.parser.add_argument('text', type=str)
    self.parser.add_argument('--delay', '-d', type=int)
    self.parser.add_argument(
      '--remember',
      '-r',
      action='store_true',
      default=False
    )
    
    self.cron_schedule = '@hourly'
  
  def command(self, msg, args):
    if args.delay:
      text = (
        f'Hello after {args.delay} seconds! I was called by {msg.author.name}'
      )
      _say_after_delay(client, msg.channel, text, args.delay, args.remember)
    else:
      return f"Hello {msg.author.name}! Here's some text: \"{args.text}\""
  
  def scheduled(self, when, now):
    for guild in self.client.guilds:
      for channel in guild.channels:
        if (
          channel.name == 'hourly-text'
          and channel.permissions_for(self.client.user).send_messages
        ):
          self.client.run_coro(channel.send(
              f"Here's your hourly text! It is hour {now.hour}."
          ))
  
  def _say_after_delay(self, location, text, delay, remember=False):
    if remember:
      self.client.schedule(delay, 0, client.run_coro, location.send(text))
    else:
      time.sleep(delay)
      location.send(text)
```
