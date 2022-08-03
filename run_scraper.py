# -*- coding: utf-8 -*-

import mechanicalsoup as ms
import os
import notify
import traceback
from urllib.parse import urljoin
import json
import pyshorteners
from pathlib import Path
import arrow

PUSH_NOTIFICATION = True
MAX_NOT_ENTRIES = 5

BROWSER = ms.StatefulBrowser()

SEARCH_URL_FILE = './search_url.in'
HITS_FILE = './hits.out'
APRTS_FILE = './aprts.out'
HISTORY_FILE = './history.txt'
MAX_PAGES = 20

HYBELNO_BASE_URL = 'https://hybel.no/'
FINNNO_BASE_URL = 'https://www.finn.no/realestate/lettings/search.html'

EMAIL = 'landsverk.vegard@gmail.com'
KEYCHAIN_NAME = 'Gmail - epostskript (gcal)'

HYBELNO_IND = 0
FINNNO_IND = 1

URL_IND = 0
SITE_IND = 1


def main():
    try:
        urls = setup()
        get_ids(urls)
    except Exception:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()


def setup():
    # Create files if not existing
    Path(APRTS_FILE).touch(exist_ok=True)
    Path(HITS_FILE).touch(exist_ok=True)
    Path(HISTORY_FILE).touch(exist_ok=True)
    Path(SEARCH_URL_FILE).touch(exist_ok=True)

    search_urls = []

    # Get search url from file
    with open(SEARCH_URL_FILE, 'r') as fp:
        url = fp.readline().strip('\n')
        if url == '':
            raise Exception('Please add url to search url file')

        while url != '':
            search_urls.append([url, HYBELNO_IND if "hybel.no" in url else FINNNO_IND])
            url = fp.readline().strip('\n')

    return search_urls


def get_ids(search_urls):
    prev_aprts = {}
    cur_aprts = {}

    for search in search_urls:
        index = search[SITE_IND]
        url = search[URL_IND]
        cur_aprts = process_page(url, cur_aprts, 1, index, url)

    with open(APRTS_FILE, 'r+') as fp:
        if fp.read() != "":
            fp.seek(0)
            try:
                prev_aprts = json.load(fp)
            except Exception as e:
                os.remove(APRTS_FILE)
                raise IOError('Could not read json. Deleting file.') from e

    with open(APRTS_FILE, 'w+') as fp:
        json.dump(cur_aprts, fp)

    # Alert if new aprts added (mere difference could be due to deletion)
    if len(cur_aprts.keys() - prev_aprts.keys()) > 0:
        alert(prev_aprts, cur_aprts, search_urls)


# Send push notification for maximum MAX_NOT_ENTRIES, and store all links in archive file
def alert(prev, curr, searches):
    new = {}
    for (aprt_id, aprt_dict) in curr.items():
        if aprt_id not in prev:
            new[aprt_id] = aprt_dict

    subj = 'Nye treff på hybel.no!'
    notify_text = f'Det er blitt lagt til {len(new)} nye annonse(r) på hybel.no-søket ditt.' \
                  f'\n\n'

    aprt_dicts = list(new.values())
    archive_links = ''
    for i in range(0, len(aprt_dicts)):
        aprt_dict = aprt_dicts[i]

        # Only store simple format in history (but store all)
        archive_links += '\n– {}\n'.format(aprt_dict["href"])
        if i >= MAX_NOT_ENTRIES:
            continue

        aprt_url = pyshorteners.Shortener().tinyurl.short(aprt_dict["href"])
        search_url = pyshorteners.Shortener().tinyurl.short(aprt_dict["search_url"])
        link = f'<a href="{aprt_url}">{aprt_dict["title"]}</a>'
        site = "hybel.no" if "hybel.no" in aprt_dict["href"] else "finn.no"
        search_link = f'<a href="{search_url}">{site}</a>'

        notify_text += f'\n{link} – {aprt_dict["rent"]} ({search_link})\n{aprt_dict["address"]}\n'

    if len(aprt_dicts) > MAX_NOT_ENTRIES:
        notify_text += f'\n... og {len(aprt_dicts) - MAX_NOT_ENTRIES} annonse(r) til.\n'

    short_urls = [pyshorteners.Shortener().tinyurl.short(url) for [url, _site] in searches]
    notify_text += f'\n\nLenke til søk:\n'

    for i in range(0, len(short_urls)):
        search_text = "Hybel.no" if searches[i][SITE_IND] == HYBELNO_IND else "Finn.no"
        notify_text += f'<a href="{short_urls[i]}">{search_text} #{i + 1}</a>\n'

    notify_text += '\nVennlig hilsen,\nHybel.no-roboten'

    if PUSH_NOTIFICATION:
        notify.push_notification(notify_text)
    else:
        notify.mail(EMAIL, subj, notify_text)
    write_to_file(archive_links)


def write_to_file(links):
    timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
    with open(HISTORY_FILE, 'a') as fp:
        fp.write(f'{timestamp}{links}\n\n')


# Scrapes pages recursively. ID used since title (in url) might change.
def process_page(page_url, aprt_dict, page_num, index, orig_url):
    page = BROWSER.get(page_url).soup

    if index == HYBELNO_IND:
        aprts = page.find_all('a', class_='card card-listing card-listing-home')
    else:
        aprts = page.find('div', class_='ads ads--list ads--cards').findAll('article')

    for aprt in aprts:

        if index == HYBELNO_IND:
            aprt_id = aprt.attrs['id']
            href = urljoin(HYBELNO_BASE_URL, aprt.attrs['href'])
            title = aprt.find('h2', class_='card-title').get_text(strip=True)  # Combine text, and strip spaces
            address = aprt.find('p').get_text("**", strip=True)
            rent = aprt.find('span', class_='listing-price').get_text("**", strip=True)
        else:
            id_title = aprt.find('div').attrs['aria-owns']
            title_h2 = aprt.find('h2', {'id': id_title})
            title_link = title_h2.contents[0]

            href = title_link.attrs['href']
            aprt_id = title_link.attrs['id']
            title = title_link.get_text(strip=True)
            address = title_h2.next_sibling.contents[0].get_text("**", strip=True)
            size_rent = title_h2.next_sibling.next_sibling.contents
            if len(size_rent) > 1:
                rent = size_rent[1].get_text("**", strip=True)
            else:
                rent = 'Ikke oppgitt'

        aprt_dict[aprt_id] = dict(
            href=href,
            title=title,
            address=address,
            rent=rent,
            search_url=orig_url
        )

    next_query = ['page-item next-page ml-gutter', 'button button--pill button--has-icon button--icon-right']
    next_page = page.find('a', class_=next_query[index])

    if next_page and page_num < MAX_PAGES:
        page_num += 1

        next_url = urljoin(HYBELNO_BASE_URL if index == HYBELNO_IND else FINNNO_BASE_URL, next_page.attrs['href'])

        process_page(next_url, aprt_dict, page_num, index, orig_url)

    return aprt_dict


if __name__ == '__main__':
    main()
