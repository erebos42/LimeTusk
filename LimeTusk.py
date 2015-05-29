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


import argparse
import subprocess
import ast
import os
import sys
import shutil
import logging
import time


TG2LY_BIN = "bin/tg2ly_0_3_0.jar"
LIMETUSK_STY = "bin/limetusk.sty"


cmd_options = None


def escape_latex(s):
    """Borrowed from PyLaTeX (MIT license). Thanks.
       https://github.com/JelteF/PyLaTeX/blob/master/pylatex/utils.py
    """
    _latex_special_chars = {
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\^{}',
        '\\': r'\textbackslash{}',
        '\n': r'\\',
        '-':  r'{-}',
        '\xA0': '~',  # Non-breaking space
    }    
    return ''.join(_latex_special_chars.get(c, c) for c in s)


class InvalidBookElementError(Exception):
    pass

class BookElement(object):
    def latex_output(self):
        raise NotImplementedError("please implement!")

    @classmethod
    def get_keyword(self):
        raise NotImplementedError("please implement!")

    @classmethod
    def _eval_file(cls, path):
        path = os.path.join(os.path.dirname(cmd_options.in_path), path)
        # TODO: what if file does not exist?!
        with open(path, 'r') as fd:
            try:
                return ast.literal_eval(fd.read().strip())
            except SyntaxError:
                raise InvalidBookElementError

    @classmethod
    def factory(cls, object_str, init_data):
        for e in BookElement.__subclasses__():
            if e.get_keyword() == object_str:
                return e(init_data)
        raise InvalidBookElementError("keyword not found")

class Chapter(BookElement):
    str_template = r"""
        \ltchapter{{{chapter_name}}}
    """

    def __init__(self, init_data):
        self.text = init_data
        super(Chapter, self).__init__()

    def __str__(self):
        return "Chapter: {}".format(self.text)

    @classmethod
    def get_keyword(self):
        return "chapter"

    def latex_output(self):
        return self.str_template.format(chapter_name=self.text)


class Song(BookElement):
    str_template = r"""
        \songheader{{{title}}}{{{artist}}}{{{album}}}{{{tuning}}}{{{composer}}}
        \lilypondfile{{{path}}}
    """

    default = {"artist": "",
               "title": "",
               "album": "",
               "tuning": "",
               "composer": "",
               "tg_file": ""}

    def __init__(self, init_path):
        init_data = BookElement._eval_file(init_path)
        
        missing_keys = Song.default.keys() - init_data.keys()
        unused_keys  = init_data.keys() - Song.default.keys()
        if missing_keys or unused_keys:
            logging.warning("Malformed input: " + str(init_path))
        if missing_keys:
            logging.warning("Missing keys: " + str(missing_keys))
        if unused_keys:
            logging.warning("Unused keys: " + str(unused_keys))
        
        self.data = Song.default.copy()
        self.data.update(init_data)
        self.data["tg_file"] = os.path.join(os.path.dirname(cmd_options.in_path), self.data["tg_file"])
        if not os.path.exists(self.data["tg_file"]):
            raise FileNotFoundError
        self.data["hash"] = self.convert()
        super(Song, self).__init__()

    def __str__(self):
        return "Song: {}".format(self.data["title"])

    @classmethod
    def get_keyword(self):
        return "song"

    def latex_output(self):
        return self.str_template.format(artist   = escape_latex(self.data["artist"]),
                                         title    = escape_latex(self.data["title"]),
                                         tuning   = escape_latex(self.data["tuning"]),
                                         album    = escape_latex(self.data["album"]),
                                         composer = escape_latex(self.data["composer"]),
                                         path     = os.path.join(cmd_options.out_path, self.data["hash"] + ".ly"))

    def convert(self):
        cmd = ["java", "-jar", TG2LY_BIN, "--in", self.data["tg_file"], "--out", cmd_options.out_path]
        out = subprocess.check_output(cmd)
        out = out.decode('utf-8').replace('\n', '')
        return out


class CSong(BookElement):
    str_template = r"""
        \begin{{songs}}{{}}
        \csongtoc{{{title}}}{{{artist}}}
        \beginsong{{{title}}}[
          by={{{artist}}},
          cr={{{composer}}},
        ]
            \musicnote{{{tuning}}}
        
            {content}
        \endsong
        \end{{songs}}
    """
    
    default = {"artist": "",
               "title": "",
               "tuning": "",
               "composer": "",
               "album": "",
               "year": "",
               "content": ""}

    def __init__(self, init_path):
        init_data = BookElement._eval_file(init_path)
        
        missing_keys = CSong.default.keys() - init_data.keys()
        unused_keys  = init_data.keys() - CSong.default.keys()
        if missing_keys or unused_keys:
            logging.warning("Malformed input: " + str(init_path))
        if missing_keys:
            logging.warning("Missing keys: " + str(missing_keys))
        if unused_keys:
            logging.warning("Unused keys: " + str(unused_keys))
        
        self.data = CSong.default.copy()
        self.data.update(init_data)
        super(CSong, self).__init__()

    def __str__(self):
        return "CSong: {}".format(self.data["title"])

    @classmethod
    def get_keyword(self):
        return "csong"

    def latex_output(self):
        return self.str_template.format(artist   = escape_latex(self.data["artist"]),
                                         title    = escape_latex(self.data["title"]),
                                         tuning   = escape_latex(self.data["tuning"]),
                                         composer = escape_latex(self.data["composer"]),
                                         content  = self.data["content"])


class Quote(BookElement):
    str_template = r"""
        \fquote{{{text}}}{{{source}}}
    """
    
    default = {"text": "",
               "source": ""}

    def __init__(self, init_path):
        init_data = BookElement._eval_file(init_path)    
        
        missing_keys = Quote.default.keys() - init_data.keys()
        unused_keys  = init_data.keys() - Quote.default.keys()
        if missing_keys or unused_keys:
            logging.warning("Malformed input: " + str(init_path))
        if missing_keys:
            logging.warning("Missing keys: " + str(missing_keys))
        if unused_keys:
            logging.warning("Unused keys: " + str(unused_keys))
        
        self.data = Quote.default.copy()
        self.data.update(init_data)
        super(Quote, self).__init__()

    def __str__(self):
        return "Quote: {}".format(self.data["source"])

    @classmethod
    def get_keyword(self):
        return "quote"

    def latex_output(self):
        return self.str_template.format(text=self.data["text"], source=self.data["source"])


class Picture(BookElement):
    str_template = r"""
        \begin{{figure}}[htb]
        {align}
        \includegraphics[{size}]{{{path}}}
        \end{{figure}}
    """

    default = {"align": "",
               "size": "",
               "pic_path": ""}

    def __init__(self, init_path):
        init_data = BookElement._eval_file(init_path)    
        
        missing_keys = Picture.default.keys() - init_data.keys()
        unused_keys  = init_data.keys() - Picture.default.keys()
        if missing_keys or unused_keys:
            logging.warning("Malformed input: " + str(init_path))
        if missing_keys:
            logging.warning("Missing keys: " + str(missing_keys))
        if unused_keys:
            logging.warning("Unused keys: " + str(unused_keys))
        
        self.data = Picture.default.copy()
        self.data.update(init_data)
        
        if self.data["align"] == "center":
            self.data["align"] = "\\centering"
        elif self.data["align"] == "right":
            self.data["align"] = "\\raggedleft"
        else:
            self.data["align"] = "\\raggedright"
        self.data["pic_path"] = os.path.join(os.path.dirname(cmd_options.in_path), self.data["pic_path"])
        self.data["pic_path"] = os.path.abspath(self.data["pic_path"])
        super(Picture, self).__init__()

    def __str__(self):
        return "Picture: {}".format(self.data["pic_path"])

    @classmethod
    def get_keyword(self):
        return "pic"

    def latex_output(self):
        return Picture.str_template.format(align=self.data["align"], size=self.data["size"], path=self.data["pic_path"])


class Title(BookElement):
    def __init__(self, init_data):
        self.title = init_data
        super(Title, self).__init__()

    def __str__(self):
        return "Title: {}".format(self.title)

    @classmethod
    def get_keyword(self):
        return "title"

    def latex_output(self):
        return ""


class Book(object):
    lytex_header_template = r"""
        \documentclass[a4paper, twoside, DIV=15, cleardoublepage=empty, final]{{scrbook}}
        \usepackage[utf8]{{inputenc}}
        \usepackage[T1]{{fontenc}}
        \usepackage[ngerman, english]{{babel}}
        \usepackage{{microtype}}
        \usepackage{{lmodern}}
        \usepackage[
            pdftex,
            bookmarks, bookmarksopen, bookmarksopenlevel=1, bookmarksnumbered=true,
            pdfpagemode={{UseNone}}, pdfpagelayout={{TwoPageRight}}, plainpages=false,
            pdfkeywords={{}}, pdfsubject={{}}, pdftitle={{}}, pdfauthor={{}},
        ]{{hyperref}}
        \usepackage{{graphicx}}
        \usepackage[nopdfindex]{{songs}}
        \usepackage{{limetusk}}
        \title{{{title}}}
        \author{{}}
        \lowertitleback{{This document was created using LilyPond and {{\LaTeX}}/{{\KOMAScript}}.\\
            The content of this book is property of their respective owners,\\
            while the document itself is licensed under the Creative Commons BY-SA 3.0 license.
        }}
        \begin{{document}}
            \maketitle
            \tableofcontents    
    """

    lytex_footer = r"""
        \end{document}
    """

    def __init__(self, book_path):
        self.book_path = book_path
        self.content = self.parse_book()
        self.title = "Songbook"
        title_list = [e for e in self.content if isinstance(e, Title)]
        if len(title_list) == 0:
            logging.warning("Title not defined. Default is being used.")
        else:
            if len(title_list) != 1:
                logging.warning("Multiple titles defines. First found used.")
            self.title = title_list[0].title

    def parse_book(self):
        ret = []
        with open(self.book_path, "r") as fd:
            line_no = 0
            for raw_line in fd:
                line_no += 1
                raw_line = raw_line.replace("\n", "")
                raw_line = raw_line.strip()
                line = raw_line.split('#')[0]
                if len(line) == 0:
                    continue
                line = line.split(":", maxsplit=1)
                try:
                    e = BookElement.factory(line[0], line[1])
                    ret.append(e)
                    logging.debug(e)
                except (InvalidBookElementError, IndexError):
                    logging.error('Invalid line {line_no}: "{line}"'.format(line_no=line_no, line=raw_line))
        return ret

    def latex_output(self):
        last_item = None
    
        ret = ""
        ret += Book.lytex_header_template.format(title=self.title)
        for e in self.content:
        
            ret += e.latex_output()
        ret += str(Book.lytex_footer)
        return ret


def parse_cmd_options():
    global cmd_options
    parser = argparse.ArgumentParser(description='Create modular and beautfiul songbooks using LilyPond and LaTeX.')
    parser.add_argument(      '--version',                  action='version',                               version='%(prog)s ' + __version__)
    parser.add_argument('-v', '--verbose', dest='verbose',  action='count'     , default=0, required=False, help="Enable verbose building process.")
    parser.add_argument('-d', '--draft',   dest='draft',    action='store_true',            required=False, help="Generate document in draft mode, to speed up testing.")
    parser.add_argument(      '--in',      dest='in_path',  action='store',                 required=True,  help="Path to the book to compile.")
    parser.add_argument(      '--out',     dest='out_path', action='store',                 required=True,  help="Path of the output directory. Will create dir if necesarry.")
    cmd_options = parser.parse_args()
    
    
def generate_lytex():
    os.makedirs(cmd_options.out_path, exist_ok=True)
    book = Book(cmd_options.in_path)
    lytex_path = os.path.join(cmd_options.out_path, book.title + ".lytex")
    with open(lytex_path, "w") as fd:
        fd.write(book.latex_output())
    return book


def generate_tex(book):
    # copy sty first, since lilypond-book tries to guess the textwidth
    shutil.copy(LIMETUSK_STY, cmd_options.out_path)
    cmd  = ["lilypond-book", "--pdf"]
    cmd += [] if cmd_options.verbose else ["--loglevel=WARN", "--lily-loglevel=WARN"]
    cmd += ["--format=latex"]
    cmd += ["--out="+cmd_options.out_path]
    cmd += [os.path.join(cmd_options.out_path, book.title + ".lytex")]
    subprocess.call(cmd)


def compile_tex(book, draft=False):
    cmd  = ["pdflatex"]
    cmd += ["-draftmode"] if draft else []
    cmd += ["-interaction=nonstopmode"]
    cmd += ["-output-directory=" + cmd_options.out_path]
    cmd += [book.title + ".tex"]
    temp_env = os.environ.copy()
    temp_env['TEXINPUTS'] = cmd_options.out_path + ":" + temp_env.get('TEXINPUTS', '')
    if cmd_options.verbose == 2:
        subprocess.call(cmd, env=temp_env)
    else:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, env=temp_env)


def check_env():
    cmd  = ["lilypond-book", "--version"]
    try:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("lilypond-book not found!")
    cmd  = ["pdflatex", "--version"]
    try:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("pdflatex not found!")
    cmd = ["java", "-jar", TG2LY_BIN, "--version"]
    try:
        ret = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret != 0:
            sys.exit("tg2ly not found!")
    except FileNotFoundError:
        sys.exit("java not found!")


def main():
    parse_cmd_options()

    log_level = logging.INFO
    if cmd_options.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)
    run_time = time.time()

    check_env()

    logging.info("Parsing book and converting songs...")
    book = generate_lytex()
    logging.info("Generating book...")
    generate_tex(book)
    logging.info("Compiling book...")
    compile_tex(book, draft=True)
    if not cmd_options.draft:
        compile_tex(book, draft=False)
    
    logging.info("Finished in {run_time:.2f} seconds".format(run_time=(time.time() - run_time)))


if __name__ == "__main__":
    main()
