#!/usr/bin/env python3

import os
import praw
import praw.models
import configparser
import sqlite3
import time
from datetime import date

from snood.ui import Spinner
from snood import telegram
import snood.util
from tqdm import tqdm
import humanfriendly
from signal import signal, SIGINT

from colorama import init, Fore, Style
init()

IS_DOCKER = True if os.environ.get('IS_DOCKER', False) == "Yes" else False
if(IS_DOCKER):
  print(f'Running inside Docker 🐋')

CONFIG_PATH = '/config/config.ini' if IS_DOCKER else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
SQLITE_PATH = '/config/database.sqlite' if IS_DOCKER else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.sqlite')

def exists_already(post: praw.models.Submission, conn: sqlite3.Connection) -> bool:
  c = conn.cursor()
  c.execute(f'SELECT COUNT(id) FROM reddit_submissions WHERE id=?', (post.id,))
  count = c.fetchall()[0]['COUNT(id)']
  if(count > 0):
    return True
  else:
    return False

def friend_already(redditor: praw.models.Redditor, conn: sqlite3.Connection) -> bool:
  c = conn.cursor()
  c.execute(f'SELECT COUNT(id) FROM redditors WHERE id=?', (redditor.id,))
  count = c.fetchall()[0]['COUNT(id)']
  if(count > 0):
    return True
  else:
    return False
  
def localize_utc(x: int) -> str:
  return date.fromtimestamp(x).strftime('%b %d, %Y')

program_execute_time = time.mktime(time.localtime())

config = configparser.ConfigParser()
# reads config.ini that's adjacent to main.py
config.read(CONFIG_PATH)

reddit = praw.Reddit(client_id=config['REDDIT']['ClientId'],
           client_secret=config['REDDIT']['ClientSecret'],
           password=config['REDDIT']['Password'], user_agent='au5ton/snood',
           username=config['REDDIT']['Username'])

friends = []
with Spinner('Loading friends from reddit'):
  friends = reddit.user.friends()

conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = snood.util.dict_factory
c = conn.cursor()

telegram.send_message('snood: indexer initializing')

with Spinner('Initializing database'):
  # PRAW should have this information lazy-loaded and follow-up requests shouldn't be necessary
  # https://praw.readthedocs.io/en/v3.6.0/pages/lazy-loading.html
  c.execute('''
  CREATE TABLE IF NOT EXISTS redditors (
  name text unique,
  id text unique,
  snood_added_utc real
  )
  ''')

  c.execute('''
  CREATE TABLE IF NOT EXISTS reddit_submissions (
  title text,
  author text,
  created_utc real,
  permalink text,
  url text,
  id text unique,
  num_comments integer,
  score integer,
  snood_added_utc real,
  snood_downloaded boolean
  )
  ''')

tmp_msgs = []
with Spinner('Populating database with redditor information'):
  for redditor in friends:
    if(not friend_already(redditor, conn)):
      tmp_msgs += [f'\t{Style.DIM}{redditor.name} is a new redditor.{Style.RESET_ALL}']
    c.execute(
      f'INSERT OR IGNORE INTO redditors VALUES {str((redditor.name, redditor.id, time.mktime(time.localtime())))}')
    conn.commit()
for ln in tmp_msgs:
  print(ln)
print(f'{Fore.GREEN}{len(tmp_msgs)} new redditors.{Style.RESET_ALL}')

# only usernames are necessary
friends = [u.name for u in friends]
print(f'Downloading post history')
with tqdm(total=len(friends), unit='user') as pbar:
  for username in friends:
    user_execute_time = time.time_ns()
    pbar.set_description(username)
    new_post_count = 0
    message = ''
    try:
      for post in reddit.redditor(username).submissions.new(limit=None):
        if post.is_self == False and post.stickied == False:
          exists = exists_already(post, conn)
          if(exists == False):
            new_post_count += 1
            c.execute(f'INSERT OR IGNORE INTO reddit_submissions VALUES (?,?,?,?,?,?,?,?,?,?)', (post.title, post.author.name, post.created_utc, f'https://reddit.com{post.permalink}', post.url, post.id, int(post.num_comments), int(post.score), time.mktime(time.localtime()), False))
            conn.commit()
          color_start = f'{Fore.GREEN}' if new_post_count > 0 else f'{Style.DIM}'
          message = f'\t{color_start}{post.author.name} had {new_post_count} new posts.'
          if(exists):
            break
      user_elapsed = time.time_ns() - user_execute_time
      if(message == ''):
        message = f'\t{Fore.RED}{username} banned, deleted, or has no posts.'
      pbar.write(f'{message} Processed in {round(user_elapsed / 1e6 / 1000, 3)}s.{Style.RESET_ALL}')
    except KeyboardInterrupt:
      exit(0)
    except Exception as err:
      # user probably deleted
      print('Unexpected error:', err)
      pass
    pbar.update()

seconds_passed = time.mktime(time.localtime()) - program_execute_time
print(f'Program took {humanfriendly.format_timespan(seconds_passed)} to complete.')
telegram.send_message(f'snood: indexer completed in {humanfriendly.format_timespan(seconds_passed)}')
