# -*- coding: utf-8 -*-

import mechanicalsoup as ms
import notify  # Local module, included in $PYTHONPATH
import traceback
from urllib.parse import urljoin
from scrape_tools import i_o_setup, get_ids, alert_write_new

PUSH_NOTIFICATION = True
EMAIL_NOTIFICATION = False

MAX_NOT_ENTRIES = 4
MAX_PAGES = 20

BROWSER = ms.StatefulBrowser()

SEARCH_URL_FILE = './in_out/hybel_no.in'
APRTS_FILE = './in_out/hybel_no.out'
HISTORY_FILE = './in_out/hybel_no.history'

HYBELNO_BASE_URL = 'https://hybel.no/'

EMAIL = 'landsverk.vegard@gmail.com'
API_TOKEN = 'a39tanxri2suyfdxczuzupt5yg5zmy'


def main():
    try:
        searches = i_o_setup(APRTS_FILE, HISTORY_FILE, SEARCH_URL_FILE)
        new_aprts = get_ids(searches, APRTS_FILE, process_page)

        if new_aprts:
            alert_write_new('Hybel.no', new_aprts, searches, aprt_string_format,
                            push_notifications=PUSH_NOTIFICATION, email_notifications=EMAIL_NOTIFICATION,
                            output_file=HISTORY_FILE, max_notif_entries=MAX_NOT_ENTRIES, api_token=API_TOKEN)
    except Exception:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()


def aprt_string_format(ad_link, search_link, ad_dict):
    return f'{ad_link} – {ad_dict["rent"]} (Søk: "{search_link}")\n{ad_dict["address"]}'


# Scrapes pages recursively. ID used since title (in url) might change.
def process_page(page_url, aprt_dict, search, page_num):
    page = BROWSER.get(page_url).soup

    aprts = page.find_all('a', class_='card card-listing card-listing-home')

    for aprt in aprts:

        aprt_id = aprt.attrs['id']
        href = urljoin(HYBELNO_BASE_URL, aprt.attrs['href'])
        title = aprt.find('h2', class_='card-title').get_text(strip=True)  # Combine text, and strip spaces
        address = aprt.find('p').get_text("**", strip=True)
        rent = aprt.find('span', class_='listing-price').get_text("**", strip=True)

        aprt_dict[aprt_id] = dict(
            href=href,
            title=title,
            address=address,
            rent=rent,
            search=search
        )

    next_page = page.find('a', class_='page-item next-page ml-gutter')

    if next_page and page_num < MAX_PAGES:
        page_num += 1
        next_url = urljoin(HYBELNO_BASE_URL, next_page.attrs['href'])
        process_page(next_url, aprt_dict, search, page_num)

    return aprt_dict


if __name__ == '__main__':
    main()
