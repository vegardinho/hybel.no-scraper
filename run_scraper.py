import os
import sys
# Include path for local python-tools (send-email etc.)
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.environ['PYTHON_TOOLS'])

import mechanicalsoup as ms
import notify
import traceback
from urllib.parse import urljoin
import json
import pyshorteners
from pathlib import Path
import arrow

PUSH_NOTIFICATION = True

BROWSER = ms.StatefulBrowser()
HITS_FILE = './hits.out'
APRTS_FILE = './aprts.out'
HISTORY_FILE = './history.txt'
MAX_PAGES = 20

SEARCH_URL = "https://hybel.no/bolig-til-leie/Oslo--Norge/?order_by=-created_at&rent_gte=&rent_lte=6500&available_from_gte=&available_from_lte=&rent_period_in=1"
BASE_URL = 'https://hybel.no/'

EMAIL = 'landsverk.vegard@gmail.com'
KEYCHAIN_NAME = 'Gmail - epostskript (gcal)'

def main():
    try:
        create_files()
        get_ids()
    except Exception as e:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()

def create_files():
    # Create files if not existing
    Path(APRTS_FILE).touch(exist_ok=True)
    Path(HITS_FILE).touch(exist_ok=True)
    Path(HISTORY_FILE).touch(exist_ok=True)


def get_ids():
    prev_aprts = {}
    cur_aprts = {}
    process_page(SEARCH_URL, cur_aprts, 1)


    with open(APRTS_FILE, 'r+') as fp:
        if fp.read() != "":
            fp.seek(0)
            prev_aprts = json.load(fp)

    with open(APRTS_FILE, 'w+') as fp:
        json.dump(cur_aprts, fp)

    #Alert if new aprts added (mere difference could be due to deletion)
    if len(cur_aprts.keys() - prev_aprts.keys()) > 0:
        alert(prev_aprts, cur_aprts)


def alert(prev, curr):
    new = {}
    for (key, val) in curr.items():
        if key not in prev:
            new[key] = val

    subj = 'Nye treff på hybel.no!'
    text = f'Det er blitt lagt til {len(new)} nye annonse(r) på hybel.no-søket ditt.' \
           f'\n\n\nNye treff:'

    for (key, val) in new.items():
        links = '\n– {}\n'.format(urljoin(BASE_URL, val))

    text += links
    short_url = pyshorteners.Shortener().tinyurl.short(SEARCH_URL)
    text += '\n\nLenke til søk:\n{}\n\n\n\n\nVennlig hilsen,\nHybel.no-roboten'.format(short_url)

    if PUSH_NOTIFICATION:
        notify.push_notification(text)
    else:
        notify.mail(EMAIL, EMAIL, KEYCHAIN_NAME, subj, text)
    write_to_file(links)

def write_to_file(links):
    timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
    with open(HISTORY_FILE, 'a') as fp:
        fp.write(f'{timestamp}{links}\n\n')



#Scrapes pages recursively. ID used since title (in url) might change.
def process_page(page_url, dict, iter):
    page = BROWSER.get(page_url).soup
    aprts = page.find_all('a', class_='card card-listing card-listing-home')
    for aprt in aprts:
        dict[aprt.attrs['id']] = aprt.attrs['href']

    next_page = page.find('a', class_='page-item next-page ml-gutter')
    if next_page and iter < MAX_PAGES:
        iter += 1
        next_url = urljoin(BASE_URL, next_page.attrs['href'])
        process_page(next_url, dict, iter)
    return


if __name__ == '__main__':
    main()





### OLD, MORE SIMPLIFIED VERSION ###
#
#
# def search_apar():
#     prev_hits = get_hits()
#
#     soup = BROWSER.get(SEARCH_URL).soup
#     new_hits = soup.find('div', class_='lead').strong.text
#     write_hits(new_hits)
#     new_hits = 100
#
#     if (prev_hits != new_hits):
#         SUBJ = 'Nye treff på hybel.no'
#         TEXT = 'Det er lagt til eller slettet annonser på hybel.no-søket ditt.\n\n' \
#                'Tidligere treff: {}\nNåværende treff: {}\n\n{}'.format(prev_hits, new_hits, )
#         send_email.send_email(EMAIL, EMAIL, KEYCHAIN_NAME, SUBJ, TEXT)
#
#
# def write_hits(new_hits):
#     with open(HITS_FILE, 'w+') as f:
#         f.write(new_hits)
#
#
# def get_hits():
#     try:
#         with open(HITS_FILE, 'r+') as f:
#             hits = f.read()
#         assert hits.isdigit()
#     except Exception as e:
#         print('Could not read previous hits')
#
#     return hits
