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

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,  # delete old text and write the new text
        'summary': 'Підстановка цитувань з попередньої версії статті',  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the 
        'tlang': 'en',
    }

    def treat_page(self) -> None:
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text    
        summary = "Підстановка цитувань з попередньої версії статті"
        
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

        # Handle {{R}} templates
        r_templates = parsed.templates
        empty_rs = {}
        for template in r_templates:
            if template.name.strip().lower() == 'r' and template.arguments:
                name = template.arguments[0].value
                empty_rs[name] = template
                if name not in tags_dict:
                    empty_tags[name] = str(template)

        if len(empty_tags):
            print(empty_tags)
            tags_replaced = 0
            stop_search = False
            revs_taken = {}

            for revision in self.current_page.revisions(content=True):
                
                if stop_search:
                    break
                try:
                    print(f'Looking through {revision.comment} by {revision.user}')
                    
                    content = revision.text
                    parsed_content = wtp.parse(content)
                except Exception as e:
                    print(e)
                    print("-" * 80)
                    print("Content")
                    print("-" * 80)
                    print(content)
                    print("-" * 80)
                    
                parsed_tags = parsed_content.get_tags(name="ref")

                tags_dict = {}
                for tag in parsed_tags:
                    if "name" in tag.attrs:
                        if len(tag.contents) == 0:
                            continue
                        tags_dict[tag.attrs["name"]] = tag
                
                for key, value in tags_dict.items():
                    if key in empty_tags:
                        print(f'Found content for {key}: {value}')
                        print("Press y to accept replacement, n to decline, s to stop search")

                        while True:
                            press_y = input().lower()
                            if press_y == "y":
                                new_ref = value.string
                                text = text.replace(empty_tags[key], new_ref, 1)
                                del empty_tags[key]
                                revs_taken[str(revision.revid)] = str(revision.user) # for edit summary
                                break
                            if press_y == "n":
                                break
                            if press_y == "s":
                                stop_search = True
                                break
                    
                    if len(empty_tags) == 0: stop_search = True
            
            summary += " (З правок: "
            for id, user in revs_taken.items():
                summary += f"{user}: https://uk.wikipedia.org/w/index.php?title={self.current_page.title()}&oldid={id} ;"
            summary += ")"

        self.put_current(text, summary=summary)


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
        if option in ('summary', 'text', 'tlang'):
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
