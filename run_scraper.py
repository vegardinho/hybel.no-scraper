import os
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.environ['PYTHON_TOOLS'])

import mechanicalsoup as ms
import notify
import traceback
from urllib.parse import urljoin
import json
import pyshorteners
from pathlib import Path

PUSH_NOTIFICATION = True

BROWSER = ms.StatefulBrowser()
HITS_FILE = './hits.out'
APRTS_FILE = './aprts.out'
MAX_PAGES = 20

SEARCH_URL = "https://hybel.no/bolig-til-leie/Oslo--Norge/?order_by=-created_at&rent_gte=&rent_lte=15000&available_from_gte=&available_from_lte=&rent_period_in=1&sub_locality_in=Frogner&sub_locality_in=Gamle+Oslo&sub_locality_in=Gr%C3%BCnerl%C3%B8kka&sub_locality_in=Majorstuen&sub_locality_in=Sagene&sub_locality_in=Sentrum&sub_locality_in=St.+Hanshaugen&housing_in=2&rooms_in=3"
BASE_URL = 'https://hybel.no/'

EMAIL = 'landsverk.vegard@gmail.com'
KEYCHAIN_NAME = 'Gmail - epostskript (gcal)'

def main():
    try:
        get_ids()
    except Exception as e:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()



def get_ids():
    prev_aprts = {}
    cur_aprts = {}
    process_page(SEARCH_URL, cur_aprts, 1)

    #Create files if not existing
    Path(APRTS_FILE).touch(exist_ok=True)
    Path(HITS_FILE).touch(exist_ok=True)

    with open(APRTS_FILE, 'r+') as fp:
        if fp.read() != "":
            fp.seek(0)
            prev_aprts = json.load(fp)

    with open(APRTS_FILE, 'w+') as fp:
        json.dump(cur_aprts, fp)

    if prev_aprts != cur_aprts:
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
        text += '\n– {}\n'.format(urljoin(BASE_URL, val))

    short_url = pyshorteners.Shortener().tinyurl.short(SEARCH_URL)
    text += '\n\nLenke til søk:\n{}\n\n\n\n\nVennlig hilsen,\nHybel.no-roboten'.format(short_url)

    if PUSH_NOTIFICATION:
        notify.push_notification(text)
    else:
        notify.mail(EMAIL, EMAIL, KEYCHAIN_NAME, subj, text)


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