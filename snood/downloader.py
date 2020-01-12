
import requests
import shutil
import os
import subprocess
from urllib.parse import urlparse

youtubedl_location = os.path.abspath(os.path.join(os.path.dirname(__file__), 'youtube-dl'))
ripme_location = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ripme.jar'))

def download_method(link: str):
    parsed = urlparse(link)
    # pure wget
    if parsed.netloc in ['i.redd.it', 'i.reddituploads.com', 'i.imgur.com', 'thumbs.gfycat.com']:
        return 'wget'
    elif 'media.tumblr.com' in parsed.netloc:
        return 'wget'
    elif (parsed.netloc == 'www.vidble.com' or parsed.netloc == 'vidble.com') and (parsed.path.endswith('.jpg') or parsed.path.endswith('.png')):
        return 'wget'
    elif parsed.netloc in ['v.redd.it', 'pornhub.com', 'www.pornhub.com', 'www.erome.com', 'erome.com', 'vimeo.com', 'www.vimeo.com', 'gfycat.com', 'www.gfycat.com']:
        return 'youtube-dl'
    elif parsed.netloc in ['imgur.com', 'm.imgur.com']:
        return 'ripme'
    elif (parsed.netloc == 'www.vidble.com' or parsed.netloc == 'vidble.com') and parsed.path.startswith('/album/'):
        return 'ripme'
    else:
        return 'other'

def wget(folder: str, link: str):
    file_name = urlparse(link).path.split('/')[-1]
    with requests.get(link, stream=True) as r:
        with open(os.path.join(os.path.abspath(folder), file_name), 'wb') as f:
            shutil.copyfileobj(r.raw, f)

def youtubedl(folder: str, link: str):
    subprocess.run([youtubedl_location, link], cwd=os.path.abspath(folder), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ripme(folder: str, link: str):
    subprocess.run(['java', '-jar', ripme_location, '-l', './', '-u', link], cwd=os.path.abspath(folder), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download(folder: str, link: str):
    if not os.path.exists(folder):
        os.mkdir(folder)
    method = download_method(link)
    if method == 'wget':
        wget(folder, link)
    elif method == 'youtube-dl':
        youtubedl(folder, link)
    elif method == 'ripme':
        ripme(folder, link)