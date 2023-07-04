import requests
from urllib.parse import urlparse, urljoin, urldefrag
from w3lib.url import canonicalize_url, url_query_cleaner
from validators import url as validate_url
from bs4 import BeautifulSoup, SoupStrainer
from playwright.sync_api import sync_playwright


strainer = SoupStrainer(['a', 'script'])


def make_soup(html):
    return BeautifulSoup(html, 'lxml', parse_only=strainer)


def scrap(url, browser):
    url = canonicalize_url(url)
    if url.endswith('/'):
        url = url[:-1]

    links = set()
    try:
        r = requests.get(url)
        if r.status_code == 200 and 'text/html' in r.headers['content-type']:
            document = make_soup(r.text)

            if document.find('script'):
                page = browser.new_page()
                page.goto(url)
                document = make_soup(page.content())
                page.close()

            for link in document.find_all('a'):
                if link.has_attr('href') and (link['href'].startswith('/') or validate_url(link['href'])):
                    url_to_add = urlparse(link['href'], allow_fragments=False)
                    if url_to_add.netloc:
                        url_to_add = url_to_add.geturl()
                    else:
                        url_to_add = urljoin(url, url_to_add.geturl())

                    url_to_add = canonicalize_url(
                        url_query_cleaner(url_to_add))
                    if url_to_add.endswith('/'):
                        url_to_add = url_to_add[:-1]

                    if url_to_add != url:
                        links.add(url_to_add)
    except:
        pass

    return links


def index(url, browser, links=set()):
    if not url in links:
        links.add(url)
        newLinks = scrap(url, browser)

        for link in newLinks:
            if not link in links:
                print(link, "from", url)
                index(link, browser, links)

        links.update(newLinks)

    return links


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        index("http://brainfuck.org", browser)
        browser.close()
