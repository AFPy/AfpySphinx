#-*- coding:utf-8 -*-
"""
A script for fetching the AFPY planet and generating an html page out of it.
"""
from base64 import b64encode
from os import path
import re
import sys

from pyquery import PyQuery


def path_from_here(*bits):
    """Return an absolute path from the given relative bits."""
    here = path.dirname(path.basename(__file__))
    return path.join(here, *bits)


LANDING_URL = 'http://www.afpy.org/'
PLANET_URL = 'http://www.afpy.org/planet/rss.xml'
FEEDICON = path_from_here('feedicon.png')

PLANET_FRAGMENT_TPL = u"""
<div id="content">
    <h1>
        Planète AFPy
        <a href="{rss_href}">
            <img alt="RSS" src="data:image/png;base64,{base64}" />
        </a>
    </h1>
{rss_items}
</div>
"""
ITEM_TPL = u"""
<h2><a href="{href}">{title}</a></h2>
<div>
    <div class="documentByLine">
        <span class="documentModified">Publié le {date}</span>
    </div>
    <blockquote>
    {body}
    </blockquote>
</div>
"""
RSS_AUTODISCOVER_TPL = u"""
<link rel="alternate" type="application/rss+xml" title="{title}" href="{href}" />
"""


def fix_self_closed_tags(html, no_self_close=('script', 'div')):
    """
    Pyquery has a bug where it will self-close tags that have no children.
    This is invalid for some tags (script and div, namely) and presumably
    triggers quirks-mode rendering in the browser, which messes with the floaty
    navigation.

    This function finds the invalid self-closed using regular expressions and
    fixes them.
    """
    # Achievement unlocked: parsing HTML with regexp
    def fix(m):
        if m.group('tagname') in no_self_close:
            fmt = '<%(tagname)s %(attrs)s></%(tagname)s>'
        else:
            fmt = '<%(tagname)s %(attrs)s/>'
        return fmt % m.groupdict()
    pattern = r'<(?P<tagname>[^ >]+)\s+(?P<attrs>[^>]+)/>'
    return re.sub(pattern, fix, html)


def fix_get_pubdate(item):
    """
    There's a bug in pyquery where just doing item('pubDate') will yield None.
    That's why we use this somehow ugly construct (falling back to plain lxml).
    """
    return item[0].find('pubDate').text


def fix_doctype(html, doctype='<!DOCTYPE html>',
                htmltag='<html xmlns="http://www.w3.org/1999/xhtml" lang="fr">'):
    """
    Pyquery will remove doctype declaration and <html> tag.
    This will add it back in.
    """
    return u"%(doctype)s\n%(html_open)s\n%(content)s\n%(html_closing)s" % {
        'doctype': doctype,
        'html_open': htmltag,
        'content': html,
        'html_closing': '</html>',
    }


def render_items(items):
    return u'\n'.join(ITEM_TPL.format(
        href=item('link').text(),
        title=item('title').text(),
        body=item('description').text(),
        date=fix_get_pubdate(item),
    ) for item in items.items())


def inject_planet(document, planet_html):
    """
    Given the html fragment corresponding to the rendered planet,
    inject it into the given document at the correct place, overriding
    the content that is already there.
    """
    main_content = document('#portal-column-content')
    main_content.html(planet_html)


def inject_rss_autodiscover(document, planet_url):
    """
    Add an rss-autodiscover tag to the <head>
    """
    html = RSS_AUTODISCOVER_TPL.format(**{
        'href': planet_url,
        'title': u'Flux RSS Planète AFPy',
    })
    tag = PyQuery(html)
    
    head = document('head')
    head.append(tag)


def remove_auth_links(document):
    """
    Some links change when the user is logged in.
    Since we scrape the landing page without a session, this would be inconsistent.
    So we just remove these elements.
    """
    document('#portal-searchbox, #portal-personaltools-wrapper').remove()


def build_planet_fragment(url):
    document = PyQuery(url, parser='xml')
    rss_items = document('item')

    with open(path_from_here('feedicon.png'), 'rb') as f:
        icon_data = b64encode(f.read())

    return PLANET_FRAGMENT_TPL.format(**{
        'rss_items': render_items(rss_items),
        'rss_href': url,
        'base64': icon_data,
    })


def make_full_page(planet_url, landing_url):
    document = PyQuery(landing_url)
    planet_fragment = build_planet_fragment(planet_url)
    remove_auth_links(document)
    inject_planet(document, planet_fragment)
    inject_rss_autodiscover(document, planet_url)

    html = document.html()

    html = fix_self_closed_tags(html)
    html = fix_doctype(html)

    return html


def main():
    if not (1 <= len(sys.argv) <= 2):
        sys.stderr.write('Usage: %s [output_file]\n' % sys.argv[0])
        sys.exit(1)

    close_at_exit = False
    if len(sys.argv) == 1:
        out = sys.stdout
    else:
        close_at_exit = True
        out = open(sys.argv[1], 'w+')

    try:
        html = make_full_page(planet_url=PLANET_URL, landing_url=LANDING_URL)
        out.write(html.encode('utf-8'))
    finally:
        if close_at_exit:
            out.close()

if __name__ == '__main__':
    main()
