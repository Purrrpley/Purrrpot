import argparse
from concurrent.futures import ThreadPoolExecutor

import requests

import discord
import discord.abc


def command(
	client: discord.Client,
	message: discord.Message,
	args: argparse.Namespace,
):
	# Multithreaded cats (only if there's multiple)
	if args.amount > 1:
		with ThreadPoolExecutor() as e:
			# `e.map()` requires that you pass an argument to the function, so 
			# we workaround that by giving it a lambda function that takes an 
			# (unused) argument and executes the right function without any 
			# arguments.
			cats = e.map(lambda _:_get_cat(), [None] * args.amount)
	else:
		cats = [_get_cat()]
	
	# Sanity check
	msg = ''
	for cat in cats:
		if not cat.ok or 'file' not in cat.json():
			msg += 'Unable to fetch cat!\n'
		else:
			msg += cat.json()['file'] + '\n'
	
	return msg.removesuffix('\n')


def _get_cat():
	return requests.get('https://aws.random.cat/meow')


def make_parser():
	parser = argparse.ArgumentParser()
	
	parser.add_argument(
		'amount',
		type=int,
		nargs='?',
		default=1,
		choices=range(1, 6),
	)
	
	return parser
