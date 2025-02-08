#!/usr/bin/env python3

from __future__ import annotations

import pywikibot
from pywikibot import i18n
from pywikibot.backports import Container
from pywikibot.bot import OptionHandler
from pywikibot.date import format_date, formatYear
from pywikibot.exceptions import APIError, Error

import time
import datetime

class BaseRevertBot(OptionHandler):

    """Base revert bot.

    Subclass this bot and override callback to get it to do something useful.
    """

    available_options = {
        'comment': 'Перенаправлення для сторінок, перейменованих без перенаправлення користувачем, на які є червоні посилання',
        'rollback': False,
        'limit': 500,
        'type': ''
    }

    def __init__(self, site=None, **kwargs) -> None:
        """Initializer."""
        self.site = site or pywikibot.Site()
        self.user = kwargs.pop('user', self.site.username())
        super().__init__(**kwargs)
        
    def page_exists(self, pagename):
        return pywikibot.Page(self.site, pagename).exists()

    def get_contributions(self, total: int = 500, ns=None):
        """Get contributions."""
        #my_stamp = time.mktime(datetime.datetime.strptime("28/03/2024", "%d/%m/%Y").timetuple())
        return pywikibot.User(self.site, self.user).logevents(logtype=self.opt.type, """start=my_stamp,""" namespace=0)

    def revert_contribs(self, callback=None) -> None:
        """Revert contributions."""
        if callback is None:
            callback = self.callback

        for item in self.get_contributions(total=self.opt.limit):
            if callback(self, item):
                result = self.revert(item)
                if result:
                    pywikibot.info(f"{item['title']}: {result}")
                else:
                    pywikibot.info(f"Skipped {item['title']}")
            else:
                pywikibot.info(f"Skipped {item['title']} by callback")

    @staticmethod
    def callback(self, item: Container) -> bool:
        """Callback function."""
        print(f'{item.page().title()} -> {item.target_title}')
        is_broken = not self.page_exists(item.page().title()) and self.page_exists(item.target_title)
        has_links = any(item.page().getReferences())

        return is_broken and has_links

    def local_timestamp(self, ts) -> str:
        """Convert Timestamp to a localized timestamp string.

        .. versionadded:: 7.0
        """
        year = formatYear(self.site.lang, ts.year)
        date = format_date(ts.month, ts.day, self.site)
        *_, time = str(ts).strip('Z').partition('T')
        return ' '.join((date, year, time))

    def revert(self, item) -> str | bool:
        """Revert a single item."""
        target_page = item.target_page
        text = target_page.text[:4000]
        
        print(text)
        check = input()
        if check == "n":
            return False
        new_page = pywikibot.Page(self.site, item.page().title())
        new_page.text = f'#ПЕРЕНАПРАВЛЕННЯ [[{item.target_title}]]'
        new_page.save(summary=self.opt.comment)
        
        return new_page.text


# for compatibility only
myRevertBot = BaseRevertBot  # noqa: N816


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        if not opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'username':
            options['user'] = value or pywikibot.input(
                'Please enter username of the person you want to revert:')
        elif opt == 'type':
            options[opt] = str(value)
        elif opt == 'rollback':
            options[opt] = True
        elif opt == 'limit':
            options[opt] = int(value)

    bot = myRevertBot(**options)
    bot.revert_contribs()


if __name__ == '__main__':
    main()
