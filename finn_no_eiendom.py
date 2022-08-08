# -*- coding: utf-8 -*-

from urllib.parse import urljoin
from scrape_tools import scrape_site


SEARCH_URL_FILE = './in_out/finn_no.in'
APRTS_FILE = './in_out/finn_no.out'
HISTORY_FILE = './in_out/finn_no.history'

FINNNO_BASE_URL = 'https://www.finn.no/realestate/lettings/search.html'
PUSHOVER_TOKEN = 'ak6z4te6odubtpb61gna4yryb3pqb5'


def main():
    scrape_site(get_elements, get_attrs, get_next_page, 'Finn.no (eiendom)', aprt_string_format,
                pushover_token=PUSHOVER_TOKEN, history_file=HISTORY_FILE,
                searches_file=SEARCH_URL_FILE, elmnts_out_file=APRTS_FILE)


def aprt_string_format(ad_link, search_link, ad_dict):
    return f'{ad_link} – {ad_dict["rent"]} ({search_link})\n{ad_dict["address"]}'


def get_elements(page):
    return page.find('div', class_='ads ads--list ads--cards').findAll('article')


def get_attrs(aprt, aprt_dict, search):
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

    return aprt_dict


def get_next_page(page):
    next_page = page.find('a', class_='button button--pill button--has-icon button--icon-right')
    if not next_page:
        return None
    return urljoin(FINNNO_BASE_URL, next_page.attrs['href'])


if __name__ == '__main__':
    main()
