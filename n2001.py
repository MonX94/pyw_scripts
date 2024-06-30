#!/usr/bin/env python3
from __future__ import annotations

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
import wikitextparser as wtp
import re
import difflib

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

def get_region_from_categories(page):
    """
    Визначає область, до якої належить населений пункт, на основі категорій статті, з урахуванням рекурсивного пошуку у батьківських категоріях.

    :param page: Сторінка Вікіпедії про населений пункт.
    :param regions_dict: Словник, що відображає категорії населених пунктів на області.
    :return: Назва області або None, якщо область не знайдена.
    """
    
    regions_dict = {
    "Населені пункти Вінницької області": "Вінницька область",
    "Населені пункти Волинської області": "Волинська область",
    "Населені пункти Дніпропетровської області": "Дніпропетровська область",
    "Населені пункти Донецької області": "Донецька область",
    "Населені пункти Житомирської області": "Житомирська область",
    "Населені пункти Закарпатської області": "Закарпатська область",
    "Населені пункти Запорізької області": "Запорізька область",
    "Населені пункти Івано-Франківської області": "Івано-Франківська область",
    "Населені пункти Київської області": "Київська область",
    "Населені пункти Кіровоградської області": "Кіровоградська область",
    "Населені пункти Луганської області": "Луганська область",
    "Населені пункти Львівської області": "Львівська область",
    "Населені пункти Миколаївської області": "Миколаївська область",
    "Населені пункти Одеської області": "Одеська область",
    "Населені пункти Полтавської області": "Полтавська область",
    "Населені пункти Рівненської області": "Рівненська область",
    "Населені пункти Сумської області": "Сумська область",
    "Населені пункти Тернопільської області": "Тернопільська область",
    "Населені пункти Харківської області": "Харківська область",
    "Населені пункти Херсонської області": "Херсонська область",
    "Населені пункти Хмельницької області": "Хмельницька область",
    "Населені пункти Черкаської області": "Черкаська область",
    "Населені пункти Чернівецької області": "Чернівецька область",
    "Населені пункти Чернігівської області": "Чернігівська область"
    }
    
    
    def check_category_recursively(category, visited):
        if category.title(with_ns=False) in regions_dict:
            return regions_dict[category.title(with_ns=False)]
        visited.add(category)
        for parent_cat in category.categories():
            if parent_cat not in visited:
                region = check_category_recursively(parent_cat, visited)
                if region:
                    return region
        return None

    visited_categories = set()
    for category in page.categories():
        region = check_category_recursively(category, visited_categories)
        if region:
            return region
    return None

class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    ConfigParserBot,  # A bot which reads options from scripts.ini setting file
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    """
    An incomplete sample bot.

    :ivar summary_key: Edit summary message key. The message that should be
        used is placed on /i18n subdirectory. The file containing these
        messages should have the same name as the caller script (i.e. basic.py
        in this case). Use summary_key to set a default edit summary message.

    :type summary_key: str
    """

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,  # delete old text and write the new text
        'summary': "Підстановка цитувань 'населення 2001 мова'",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text
        text_to_add = self.opt.text
        
        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        # Retrieve your private option
        # Use your own text or use the default 'Test'
        
        print(self.current_page.extract(lines=2))
        parsed = wtp.parse(text)
        tags = parsed.get_tags(name="ref")
        tags_dict = {} # only ref tags
        empty_tags = {} # all tags; name (str): stringified tag/template (str)

        # Handle <ref> tags
        for tag in tags:
            if "name" in tag.attrs:
                name = tag.attrs["name"].replace("/", "")
                
                # Only update tags_dict if the tag's contents are not empty or not already in tags_dict
                if name not in tags_dict or len(tags_dict[name].contents) == 0:
                    if len(tag.contents) == 0:
                        empty_tags[name] = str(tag)
                    tags_dict[name] = tag
                
                # Remove from empty_tags if we now have a tag with contents
                if name in empty_tags and len(tag.contents) != 0:
                    empty_tags.pop(name)

        if "населення 2001 мова" in empty_tags:
            region = get_region_from_categories(self.current_page)
            if region == None:
                print("region not found")
            else:
                print(region)
                print(empty_tags)
                text = text.replace(empty_tags["населення 2001 мова"], '<ref name="населення 2001 мова">{{БД Держстату України|тип=2001 мова|регіон=' + region + '}}</ref>')
                
        self.put_current(text, summary=self.opt.summary)

def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process pagegenerators arguments
    local_args = gen_factory.handle_args(local_args)

    # Parse your own command line arguments
    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    gen = gen_factory.getCombinedGenerator(preload=True)

    # check if further help is needed
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        # pass generator and private options to the bot
        bot = BasicBot(generator=gen, **options)
        bot.run()  # guess what it does


if __name__ == '__main__':
    main()
