from halo import Halo
from colorama import init, Fore, Style
init()

class Spinner(object):
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        self.spinner = Halo(text=self.message, spinner='bouncingBar')
        self.spinner.start()

    def __exit__(self, exception_type, exception_value, traceback):
        if(exception_type):
            self.spinner.stop_and_persist(symbol=f'[{Fore.RED}fail{Style.RESET_ALL}]')
        else:
            self.spinner.stop_and_persist(symbol=f'[ {Fore.GREEN}ok{Style.RESET_ALL} ]')