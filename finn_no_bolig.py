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

SEARCH_URL_FILE = './in_out/finn_no.in'
APRTS_FILE = './in_out/finn_no.out'
HISTORY_FILE = './in_out/finn_no.history'

FINNNO_BASE_URL = 'https://www.finn.no/realestate/lettings/search.html'

EMAIL = 'landsverk.vegard@gmail.com'
API_TOKEN = 'ak6z4te6odubtpb61gna4yryb3pqb5'


def main():
    try:
        searches = i_o_setup(APRTS_FILE, HISTORY_FILE, SEARCH_URL_FILE)
        new_aprts = get_ids(searches, APRTS_FILE, process_page)

        if new_aprts:
            alert_write_new('Finn.no - eiendom', new_aprts, searches, aprt_string_format,
                            push_notifications=PUSH_NOTIFICATION, email_notifications=EMAIL_NOTIFICATION,
                            output_file=HISTORY_FILE, max_notif_entries=MAX_NOT_ENTRIES, api_token=API_TOKEN)
    except Exception:
        notify.mail(EMAIL, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        traceback.print_exc()


def aprt_string_format(ad_link, search_link, ad_dict):
    return f'{ad_link} – {ad_dict["rent"]} ({search_link})\n{ad_dict["address"]}'


# Scrapes pages recursively. ID used since title (in url) might change.
def process_page(page_url, aprt_dict, search, page_num):
    page = BROWSER.get(page_url).soup

    aprts = page.find('div', class_='ads ads--list ads--cards').findAll('article')

    for aprt in aprts:

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
            search=search
        )

    next_page = page.find('a', class_='button button--pill button--has-icon button--icon-right')

    if next_page and page_num < MAX_PAGES:
        page_num += 1
        next_url = urljoin(FINNNO_BASE_URL, next_page.attrs['href'])
        process_page(next_url, aprt_dict, search, page_num)

    return aprt_dict


if __name__ == '__main__':
    main()
