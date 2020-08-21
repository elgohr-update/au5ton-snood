#!/usr/bin/env python3

import os
import sqlite3
import time
import argparse

from snood.ui import Spinner
import snood.downloader
import snood.util
from tqdm import tqdm
import humanfriendly
from signal import signal, SIGINT

# def handler(signal_received, frame):
#   # Handle any cleanup here
#   print('SIGINT or CTRL-C detected. Exiting gracefully')
#   exit(0)
#   #os.system(f'kill {os.getpid()}')

#signal(SIGINT, handler)

program_execute_time = time.mktime(time.localtime())

parser = argparse.ArgumentParser(description='Rip links from the database')
parser.add_argument('download_dir', type=str, help='location where files will be downloaded')
args = parser.parse_args()
print(f'Download directory: {os.path.abspath(args.download_dir)}')
DOWNLOAD_DIR = os.path.abspath(args.download_dir)

conn = sqlite3.connect('database.sqlite')
conn.row_factory = snood.util.dict_factory
c = conn.cursor()
submissions = []

with Spinner('Querying database for posts to traverse'):
  c.execute('SELECT * FROM reddit_submissions WHERE snood_downloaded = 0 ORDER BY author, created_utc ASC')
  submissions = c.fetchall()

print(f'{len(submissions)} posts queued to process')

with tqdm(total=len(submissions), unit='posts') as pbar:
  for post in submissions:
    try:
      pbar.set_description(f'/u/{post["author"]} https://redd.it/{post["id"]}')
      snood.downloader.download(os.path.join(DOWNLOAD_DIR, post['author']), post['url'])
      c.execute('UPDATE reddit_submissions SET snood_downloaded = 1 WHERE id = ?', (post["id"],))
      conn.commit()
      pbar.update()
    except KeyboardInterrupt:
      exit(0)

seconds_passed = time.mktime(time.localtime()) - program_execute_time
print(f'Program took {humanfriendly.format_timespan(seconds_passed)} to complete.')
