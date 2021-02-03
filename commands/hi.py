import argparse
from asyncio import run_coroutine_threadsafe as run_coro_safe

import discord
import discord.abc


def command(
	client: discord.Client,
	message: discord.Message,
	namespace: argparse.Namespace
):
	users = namespace.users
	users_amount = len(users)
	
	# The generated string is different depending on the amount of users:
	# '' -> ', {author}'
	# 'user' -> ', user'
	# 'user1 user2' -> ' user1 and user2'
	# 'user1 user2 ... userN' -> ' user1, user2, ..., userN'
	if users_amount == 0:
		users_str = f', {message.author.name}'
		# users_str = f', name'
	elif users_amount == 1:
		users_str = f', {users[0]}'
	elif users_amount == 2:
		users_str = f' {users[0]} and {users[1]}'
	else:
		users_str = f' {", ".join(users[:-1])}, and {users[-1]}'
	
	# send_message(client, message.channel, f'Hello{users_str}!')
	# print(f'Hello{users_str}!')
	run_coro_safe(message.channel.send(f'Hello{users_str}!'), client.loop)


def arg_parser():
	parser = argparse.ArgumentParser()
	
	parser.add_argument('users', type=str, nargs='*')
	
	return parser

# command('', '', arg_parser().parse_args('user1 user2 user3'.split()))
