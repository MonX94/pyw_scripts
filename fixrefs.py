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
        'summary': "Виправлення дублювання цитувань",  # your own bot summary
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
        
        for template in parsed.templates:
            if template.name.strip().lower() == 'bots' or template.name.strip().lower() == 'nobots': return None # don't do anything if the page is exempt

        
        tags = parsed.get_tags(name="ref")
        tags_dict = {}
        for tag in tags:
            if "name" in tag.attrs:
                if tag.attrs["name"] in tags_dict:
                    existing_tag = tags_dict[tag.attrs["name"]]
                    # Only trigger conflict resolution if both tags are non-empty
                    if len(tag.contents) == 0 or len(existing_tag.contents) == 0:
                        continue
                    if tag.contents == existing_tag.contents:
                        continue
                    print("Tag conflict!")
                    tag1 = existing_tag
                    tag2 = tag
                    print(f'Tag 1:\n {tag1}')
                    print(f'Tag 2:\n {tag2}')
                    
                    l1 = tag1.contents
                    l2 = tag2.contents
                    
                    print("Pick one: (3 - skip, 4 - diff)")
                    
                    tag_chosen = "0"
                    while tag_chosen not in ["1", "2", "3", "4"]:
                        tag_chosen = input()
                        if tag_chosen == "1":
                            text = text.replace(f'>{l2}</ref', '/')
                        elif tag_chosen == "2":
                            text = text.replace(f'>{l1}</ref', '/')
                            tags_dict[tag1.attrs["name"]] = tag2
                        elif tag_chosen == "3":
                            break
                        elif tag_chosen == "4":
                            difference = difflib.Differ()
                            for line in difference.compare(l1.splitlines(keepends=True), l2.splitlines(keepends=True)):
                                print(" ")
                                print(line, end="")
                else:
                    # Only add non-empty tags to the dictionary
                    if len(tag.contents) > 0:
                        tags_dict[tag.attrs["name"]] = tag
         
        # if summary option is None, it takes the default i18n summary from
        # i18n subdirectory with summary_key as summary key.
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
