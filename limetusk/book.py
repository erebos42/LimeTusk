import logging
import os
from limetusk.elements import BookElement, InvalidBookElementError
from limetusk.elements import Title, CSong


class BookOptions(object):
    def __init__(self, in_path, out_path, midi=False, draft=False, verbose=0):
        self.in_path  = in_path
        self.out_path = out_path
        self.midi     = midi
        self.draft    = draft
        self.verbose  = verbose


class Book(object):
    # TODO: attachfile only needed, if --midi is set
    lytex_header_template = r"""
        \documentclass[a4paper, twoside, DIV=15, cleardoublepage=empty, final]{{scrbook}}
        \usepackage[utf8]{{inputenc}}
        \usepackage[T1]{{fontenc}}
        \usepackage[ngerman, english]{{babel}}
        \usepackage{{microtype}}
        \usepackage{{lmodern}}
        \usepackage{{graphicx}}
        \usepackage[nopdfindex]{{songs}}
        \usepackage{{limetusk}}
        \usepackage[
            pdftex,
            bookmarks, bookmarksopen, bookmarksopenlevel=1, bookmarksnumbered=true,
            pdfpagemode={{UseNone}}, pdfpagelayout={{TwoPageRight}}, plainpages=false,
            pdfkeywords={{}}, pdfsubject={{}}, pdftitle={{}}, pdfauthor={{}},
        ]{{hyperref}}
        \usepackage{{attachfile}}
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

    def __init__(self, book_path, options):
        self.book_path = book_path
        self.options   = options
        self.base_path = os.path.dirname(book_path)

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
                    e = BookElement.factory(self.base_path, self.options, line[0], line[1])
                    ret.append(e)
                    logging.debug(e)
                except (InvalidBookElementError, IndexError):
                    logging.error('Invalid line {line_no}: "{line}"'.format(line_no=line_no, line=raw_line))
        return ret

    def latex_output(self):
        # TODO: change begin_env/end_env stuff more generally
        last_item = None
        ret = ""
        ret += Book.lytex_header_template.format(title=self.title)
        for e in self.content:
            if (not isinstance(last_item, CSong)) and isinstance(e, CSong):
                ret += CSong.begin_env()
            ret += e.latex_output()
            if isinstance(last_item, CSong) and (not isinstance(e, CSong)):
                ret += CSong.end_env()
            last_item = e
        if isinstance(last_item, CSong):
            ret += CSong.end_env()
        ret += str(Book.lytex_footer)
        return ret

