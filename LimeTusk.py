#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""Create modular and beautfiul songbooks using LilyPond and LaTeX."""

__version__ = '0.1.0'

# TODO
# - draft mode
# - check latex packages by compiling minimal document
# - move generation stuff into separate class
# - Fix escaping of special characters. Either input in LaTeX format, or utf-8 to LaTeX converter (must handle csong commands)
# - rewrite the 'get default infos from dict' stuff.
# - group songs environments, so the page break is better
# - write to tempdir if out not set

import argparse
import logging
import time
import os
import sys
from limetusk import util
from limetusk.book import Book, BookOptions
from limetusk.book_builder import BookBuilder


def parse_cmd_options():
    parser = argparse.ArgumentParser(description='Create modular and beautfiul songbooks using LilyPond and LaTeX.')
    parser.add_argument(      '--version',                  action='version',                               version='%(prog)s ' + __version__)
    parser.add_argument('-v', '--verbose', dest='verbose',  action='count'     , default=0, required=False, help="Enable verbose building process.")
    parser.add_argument('-d', '--draft',   dest='draft',    action='store_true',            required=False, help="Generate document in draft mode, to speed up testing.")
    parser.add_argument(      '--in',      dest='in_path',  action='store',                 required=True,  help="Path to the book to compile.")
    parser.add_argument(      '--out',     dest='out_path', action='store',                 required=True,  help="Path of the output directory. Will create dir if necesarry.")
    parser.add_argument(      '--midi',    dest='midi',     action='store_true',            required=False, help="Generate midi files for songs and attach them in the output file. Note: attachments in pdfs aren't very well supported by many viewers.")
    cmd_options = parser.parse_args()
    return BookOptions(cmd_options.in_path, cmd_options.out_path, cmd_options.midi, cmd_options.draft, cmd_options.verbose)

def main():
    options = parse_cmd_options()

    if options.verbose:
        log_level = logging.DEBUG
    run_time = time.time()

    try:
        util.check_env()
    except FileNotFoundError as e:
        sys.exit(e)

    logging.info("Parsing book and converting songs...")
    book = Book(options.in_path, options)
    builder = BookBuilder(book, options)
    builder.build()
    
    logging.info("Finished in {run_time:.2f} seconds".format(run_time=(time.time() - run_time)))


if __name__ == "__main__":
    main()
