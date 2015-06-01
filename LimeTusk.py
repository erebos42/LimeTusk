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
from limetusk import util
from limetusk.book import Book, BookOptions
from limetusk.book_builder import BookBuilder

cmd_options = None


def parse_cmd_options():
    global cmd_options
    parser = argparse.ArgumentParser(description='Create modular and beautfiul songbooks using LilyPond and LaTeX.')
    parser.add_argument(      '--version',                  action='version',                               version='%(prog)s ' + __version__)
    parser.add_argument('-v', '--verbose', dest='verbose',  action='count'     , default=0, required=False, help="Enable verbose building process.")
    parser.add_argument('-d', '--draft',   dest='draft',    action='store_true',            required=False, help="Generate document in draft mode, to speed up testing.")
    parser.add_argument(      '--in',      dest='in_path',  action='store',                 required=True,  help="Path to the book to compile.")
    parser.add_argument(      '--out',     dest='out_path', action='store',                 required=True,  help="Path of the output directory. Will create dir if necesarry.")
    parser.add_argument(      '--midi',    dest='midi',     action='store_true',            required=False, help="Generate midi files for songs and attach them in the output file. Note: attachments in pdfs aren't very well supported by many viewers.")
    cmd_options = parser.parse_args()
    # TODO: Namespace to set/dict -> vars(cmd_options)


def main():
    parse_cmd_options()

    log_level = logging.INFO
    if cmd_options.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)
    run_time = time.time()

    util.check_env()

    # TODO: make sure out dir exists before running tg2ly (this should be done in the builder)
    os.makedirs(cmd_options.out_path, exist_ok=True)
    
    # TODO: split loading from generating from compiling

    options = BookOptions(cmd_options.in_path, cmd_options.out_path, cmd_options.midi, cmd_options.draft, cmd_options.verbose)
    book = Book(cmd_options.in_path, options)
    builder = BookBuilder(book, options)
    builder.build()
    
    logging.info("Finished in {run_time:.2f} seconds".format(run_time=(time.time() - run_time)))


if __name__ == "__main__":
    main()
