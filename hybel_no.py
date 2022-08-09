# -*- coding: utf-8 -*-

from urllib.parse import urljoin
from scrape_tools import scrape_site


SEARCH_URL_FILE = './in_out/hybel_no.in'
APARTS_FILE = './in_out/hybel_no.out'
HISTORY_FILE = './in_out/hybel_no.history'

HYBEL_NO_BASE_URL = 'https://hybel.no/'
PUSHOVER_TOKEN = 'a39tanxri2suyfdxczuzupt5yg5zmy'


def main():
    scrape_site(get_elements, get_attrs, get_next_page, 'Hybel.no', aprt_string_format,
                pushover_token=PUSHOVER_TOKEN, history_file=HISTORY_FILE,
                searches_file=SEARCH_URL_FILE, elmnts_out_file=APARTS_FILE)


def aprt_string_format(ad_link, search_link, ad_dict):
    return f'{ad_link} – {ad_dict["rent"]} ({search_link})\n{ad_dict["address"]}'


def get_elements(page):
    return page.find_all('a', class_='card card-listing card-listing-home')


def get_attrs(aprt, aprt_dict, search):
    aprt_id = aprt.attrs['id']
    href = urljoin(HYBEL_NO_BASE_URL, aprt.attrs['href'])
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


    return aprt_dict


def get_next_page(page, _page_url):
    next_page = page.find('a', class_='page-item next-page ml-gutter')

    if not next_page:
        return None
    return urljoin(HYBEL_NO_BASE_URL, next_page.attrs['href'])


if __name__ == '__main__':
    main()
