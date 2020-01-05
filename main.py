#!/usr/bin/env python3

import os
import praw
import configparser
import sqlite3
import time

from snood.ui import Spinner
import snood.util
from tqdm import tqdm
import humanfriendly

program_execute_time = time.mktime(time.localtime())

config = configparser.ConfigParser()
# reads config.ini that's adjacent to main.py
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))

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
        snood_added_utc integer
        )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS reddit_submissions (
        title text,
        author text,
        created_utc integer,
        permalink text,
        url text,
        id text unique,
        num_comments integer,
        score integer,
        snood_added_utc integer,
        snood_downloaded boolean
        )
    ''')

with Spinner('Populating database with redditor information'):
    for redditor in friends:
        c.execute(f'INSERT OR IGNORE INTO redditors VALUES {str((redditor.name, redditor.id, time.mktime(time.localtime())))}')
        conn.commit()

# only usernames are necessary
friends = [u.name for u in friends]
print(f'Downloading post history')
with tqdm(total=len(friends), unit='user') as pbar:
    for username in friends:
        pbar.set_description(username)
        try:
            for post in tqdm(reddit.redditor(username).submissions.new(limit=None), total=1000, unit='post', leave=False):
                if post.is_self == False:
                    c.execute(f'INSERT OR IGNORE INTO reddit_submissions VALUES (?,?,?,?,?,?,?,?,?, ?)', (post.title, post.author.name, int(post.created_utc), f'https://reddit.com{post.permalink}', post.url, post.id, int(post.num_comments), int(post.score), time.mktime(time.localtime()), False))
                    conn.commit()
        except:
            # user probably deleted
            pass
        pbar.update()

seconds_passed = time.mktime(time.localtime()) - program_execute_time
print(f'Program took {humanfriendly.format_timespan(seconds_passed)} to complete.')
