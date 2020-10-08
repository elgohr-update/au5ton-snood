import os
import json
import requests
import configparser

from colorama import init, Fore, Style
init()

IS_DOCKER = True if os.environ.get('IS_DOCKER', False) == "Yes" else False
CONFIG_PATH = '/config/config.ini' if IS_DOCKER else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

ENDPOINT = f'https://api.telegram.org/bot{config["TELEGRAM"]["BotToken"]}/sendMessage'
CHAT_ID = config['TELEGRAM']['ChatId']


def send_message(text: str):
    with requests.get(ENDPOINT, params={ "chat_id": CHAT_ID, "text": text }) as r:
        if json.loads(r.text)["ok"] == False:
            print(f'{Fore.RED}Error sending Telegram message: {Style.RESET_ALL}', end='')
            print(f'{Style.DIM}{r.text}{Style.RESET_ALL}')
        else:
            print(f'{Fore.CYAN}📧 Telegram message sent.{Style.RESET_ALL}')