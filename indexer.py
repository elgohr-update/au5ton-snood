#!/usr/bin/env python3

import os
import praw
import praw.models
import configparser
import sqlite3
import time
from datetime import date

from snood.ui import Spinner
import snood.util
from tqdm import tqdm
import humanfriendly
from signal import signal, SIGINT

def exists_already(post: praw.models.Submission, conn: sqlite3.Connection) -> bool:
  c = conn.cursor()
  c.execute(f'SELECT COUNT(id) FROM reddit_submissions WHERE id=?', (post.id,))
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
config.read(os.path.join(os.path.dirname(
  os.path.abspath(__file__)), 'config.ini'))

reddit = praw.Reddit(client_id=config['REDDIT']['ClientId'],
           client_secret=config['REDDIT']['ClientSecret'],
           password=config['REDDIT']['Password'], user_agent='au5ton/snood',
           username=config['REDDIT']['Username'])

friends = []
with Spinner('Loading friends from reddit'):
  friends = reddit.user.friends()

conn = sqlite3.connect('database.sqlite')
conn.row_factory = snood.util.dict_factory
c = conn.cursor()

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

with Spinner('Populating database with redditor information'):
  for redditor in friends:
    c.execute(
      f'INSERT OR IGNORE INTO redditors VALUES {str((redditor.name, redditor.id, time.mktime(time.localtime())))}')
    conn.commit()

# only usernames are necessary
friends = [u.name for u in friends]
print(f'Downloading post history')
with tqdm(total=len(friends), unit='user') as pbar:
  for username in friends:
    pbar.set_description(username)
    new_post_count = 0
    message = ''
    try:
      for post in reddit.redditor(username).submissions.new(limit=None):
        if post.is_self == False:
          exists = exists_already(post, conn)
          if(exists == False):
            new_post_count += 1
          if(post.stickied or not exists):
            c.execute(f'INSERT OR IGNORE INTO reddit_submissions VALUES (?,?,?,?,?,?,?,?,?,?)', (post.title, post.author.name, post.created_utc, f'https://reddit.com{post.permalink}', post.url, post.id, int(post.num_comments), int(post.score), time.mktime(time.localtime()), False))
            conn.commit()
          message = f'\t{post.author.name} had {new_post_count} new posts. Already indexed up to {localize_utc(post.created)}.'
          if(exists and not post.stickied):
            break
      pbar.write(message)
    except KeyboardInterrupt:
      exit(0)
    except Exception as err:
      # user probably deleted
      print('Unexpected error:', err)
      pass
    pbar.update()

seconds_passed = time.mktime(time.localtime()) - program_execute_time
print(f'Program took {humanfriendly.format_timespan(seconds_passed)} to complete.')
