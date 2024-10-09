from bs4 import BeautifulSoup
from minify_html import minify_html

# Yomgui's HTML minimizer
def remove_cruft(html: str, minify: bool = False) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    for elem in soup.select("noscript, svg, style, script[type!='application/ld+json'], iframe"):
        elem.decompose()

    html = str(soup)

    if not minify:
        return html

    return minify_html.minify(html)


