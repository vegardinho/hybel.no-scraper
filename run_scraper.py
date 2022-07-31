import mechanicalsoup as ms
# import notify
import traceback
from urllib.parse import urljoin
import json
import pyshorteners
from pathlib import Path
import arrow
import os

PUSH_NOTIFICATION = True
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

def main():
    try:
        urls = setup()
        get_ids(urls)
    except Exception as e:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()

def setup():
    # Create files if not existing
    Path(APRTS_FILE).touch(exist_ok=True)
    Path(HITS_FILE).touch(exist_ok=True)
    Path(HISTORY_FILE).touch(exist_ok=True)
    Path(SEARCH_URL_FILE).touch(exist_ok=True)

    search_urls = []

    #Get search url from file
    with open(SEARCH_URL_FILE, 'r') as fp:
        url = fp.readline().strip('\n')
        if url == '':
            raise Exception('Please add url to search url file')

        while url != '':
            search_urls.append(url)
            url = fp.readline().strip('\n')

    return search_urls


def get_ids(search_urls):
    prev_aprts = {}
    cur_aprts = {}

    for url in search_urls:
        index = HYBELNO_IND if 'hybel.no' in url else FINNNO_IND
        cur_aprts = process_page(url, cur_aprts, 1, index)

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

    #Alert if new aprts added (mere difference could be due to deletion)
    if len(cur_aprts.keys() - prev_aprts.keys()) > 0:
        alert(prev_aprts, cur_aprts)


def alert(prev, curr):
    new = {}
    for (aprt_id, aprt_dict) in curr.items():
        if aprt_id not in prev:
            new[aprt_id] = aprt_dict

    subj = 'Nye treff på hybel.no!'
    text = f'Det er blitt lagt til {len(new)} nye annonse(r) på hybel.no-søket ditt.' \
           f'\n\n\nNye treff:'

    links = ''
    for (aprt_id, aprt_dict) in new.items():
        links += '\n– {}\n'.format(aprt_dict['href'])

    text += links
    short_url = pyshorteners.Shortener().tinyurl.short(search_url)
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
def process_page(page_url, aprt_dict, page_num, index):
    page = BROWSER.get(page_url).soup

    if index == HYBELNO_IND:
        aprts = page.find_all('a', class_='card card-listing card-listing-home')
    else:
        aprts = page.find('div', class_='ads ads--list ads--cards').findAll('article')

    for aprt in aprts:

        if index == HYBELNO_IND:
            aprt_id = aprt.attrs['id']
            href = urljoin(HYBELNO_BASE_URL, aprt.attrs['href'])
            title = aprt.find('h2', class_='card-title').string
            address = aprt.find('p').string.strip()
            rent = aprt.find('span', class_='listing-price').string.replace('\xa0', '')
        else:
            id_title = aprt.find('div').attrs['aria-owns']
            title_h2 = aprt.find('h2', {'id': id_title})
            title_link = title_h2.contents[0]

            href = title_link.attrs['href']
            aprt_id = title_link.attrs['id']
            title = title_link.string
            address = title_h2.next_sibling.contents[0].string
            size_rent = title_h2.next_sibling.next_sibling.contents
            if len(size_rent) > 1:
                rent = size_rent[1].string.replace('\xa0', '')
            else:
                rent = 'Ikke oppgitt'

        aprt_dict[aprt_id] = dict(
            href=href,
            title=title,
            address=address,
            rent=rent
        )

    next_query = ['page-item next-page ml-gutter', 'button button--pill button--has-icon button--icon-right']
    next_page = page.find('a', class_=next_query[index])

    if next_page and page_num < MAX_PAGES:
        page_num += 1

        next_url = urljoin(HYBELNO_BASE_URL if HYBELNO_IND else FINNNO_BASE_URL, next_page.attrs['href'])

        process_page(next_url, aprt_dict, page_num, index)

    return aprt_dict


if __name__ == '__main__':
    main()

