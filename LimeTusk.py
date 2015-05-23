#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import argparse
import subprocess
import ast
import os
import shutil

TG2LY_BIN = "bin/tg2ly_0_3_0.jar"
LIMETUSK_STY = "bin/limetusk.sty"

class BookElement(object):
    def latex_output(self):
        raise NotImplementedError("please implement!")

    @classmethod
    def _eval_file(cls, path):
        with open(path, 'r') as fd:
            return ast.literal_eval(fd.read().strip())

    @classmethod
    def factory(cls, object_str, init_data):
        data_path = os.path.join(cmd_options.in_path, init_data)
        if object_str == "chapter":
            return Chapter(init_data)
        elif object_str == "song":
            try:
                init_data = BookElement._eval_file(data_path)
                return Song(init_data)
            except FileNotFoundError:
                return None
        elif object_str == "csong":
            try:
                init_data = BookElement._eval_file(data_path)
                return CSong(init_data)
            except FileNotFoundError:
                return None
        elif object_str == "quote":
            try:
                init_data = BookElement._eval_file(data_path)
                return Quote(init_data)
            except FileNotFoundError:
                return None
        elif object_str == "pic":
            try:
                init_data = BookElement._eval_file(data_path)
                return Picture(init_data)
            except FileNotFoundError:
                return None
        else:
            return None


class Chapter(BookElement):
    str_template = r"""
        \chapter{{{chapter_name}}}
    """

    def __init__(self, init_data):
        self.text = init_data

    def latex_output(self):
        return self.str_template.format(chapter_name=self.text)


class Song(BookElement):
    str_template = r"""
        \songheader{{{title}}}{{{artist}}}{{{album}}}{{{tuning}}}{{{composer}}}
        \lilypondfile{{{path}}}
    """

    def __init__(self, init_data):
        self.artist   = init_data["artist"]
        self.title    = init_data["title"]
        self.album    = init_data["album"]
        self.tuning   = init_data["tuning"]
        self.composer = init_data["composer"]
        self.file     = os.path.join(cmd_options.in_path, init_data["tg_file"])
        if not os.path.exists(self.file):
            raise FileNotFoundError
        self.hash = self.convert()

    def latex_output(self):
        return self.str_template.format(artist   = self.artist,
                                         title    = self.title,
                                         tuning   = self.tuning,
                                         album    = self.album,
                                         composer = self.composer,
                                         path     = os.path.join(cmd_options.out_path, self.hash + ".ly"))

    def convert(self):
        cmd = ["java", "-jar", TG2LY_BIN, "--in", self.file, "--out", cmd_options.out_path]
        out = subprocess.check_output(cmd)
        out = out.decode('utf-8').replace('\n', '')
        return out

class CSong(BookElement):
    str_template = r"""
        \begin{{songs}}{{}}
        \beginsong{{{title}}}[
          by={{{artist}}},
          cr={{{composer}}},
        ]
            \musicnote{{{tuning}}}
        
            {content}
        \endsong
        \end{{songs}}
    """

    def __init__(self, init_data):
        self.artist   = init_data["artist"]
        self.title    = init_data["title"]
        self.tuning   = init_data["tuning"]
        self.composer = init_data["composer"]
        self.content  = init_data["content"]

    def latex_output(self):
        return self.str_template.format(artist   = self.artist,
                                         title    = self.title,
                                         tuning   = self.tuning,
                                         composer = self.composer,
                                         content  = self.content)


class Quote(BookElement):
    str_template = r"""
        \fquote{{{text}}}{{{source}}}
    """

    def __init__(self, init_data):
        self.text = init_data["text"]
        self.source = init_data["source"]

    def latex_output(self):
        return self.str_template.format(text=self.text, source=self.source)


class Picture(BookElement):
    str_template = r"""
        \begin{{figure}}[htb]
        {align}
        \includegraphics[{size}]{{{path}}}
        \end{{figure}}
    """

    def __init__(self, init_data):
        if init_data["align"] == "center":
            self.align = "\\centering"
        elif init_data["align"] == "right":
            self.align = "\\raggedleft"
        else:
            self.align = "\\raggedright"
        self.size = init_data["size"]
        self.pic_path = os.path.join(cmd_options.in_path, init_data["pic_path"])
        self.pic_path = os.path.abspath(self.pic_path)

    def latex_output(self):
        return Picture.str_template.format(align=self.align, size=self.size, path=self.pic_path)


class Book(object):
    lytex_header = r"""
        \documentclass[a4paper, twoside, DIV=15, cleardoublepage=empty, final]{scrbook}
        \usepackage[utf8]{inputenc}
        \usepackage[T1]{fontenc}
        \usepackage[ngerman, english]{babel}
        \usepackage{microtype}
        \usepackage{lmodern}
        \usepackage[
            pdftex,
            bookmarks, bookmarksopen, bookmarksopenlevel=1, bookmarksnumbered=true,
            pdfpagemode={UseNone}, pdfpagelayout={TwoPageRight}, plainpages=false,
            pdfkeywords={}, pdfsubject={}, pdftitle={}, pdfauthor={},
        ]{hyperref}
        \usepackage{graphicx}
        \usepackage{songs}
        \usepackage{limetusk}
        \usepackage{scrhack}
        \title{Tabbook}
        \author{}
        \lowertitleback{This document was created using LilyPond and {\LaTeX}/{\KOMAScript}.\\
            The content of this book is property of their respective owners,\\
            while the document itself is licensed under the Creative Commons BY-SA 3.0 license.
        }
        \begin{document}
            \maketitle
            \tableofcontents    
    """

    lytex_footer = r"""
        \end{document}
    """

    def __init__(self, book_path):
        self.book_path = book_path
        self.content = self.parse_book()

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
                line = line.split(":")
                if len(line) != 2:
                    print("Error parsing line {line_no}: {line}".format(line_no=line_no, line=raw_line))
                    continue
                temp = BookElement.factory(line[0], line[1])
                if temp:
                    ret.append(temp)
                else:
                    print("Error parsing line {line_no}: {line}".format(line_no=line_no, line=raw_line))
        return ret
        
    def latex_output(self):
        ret = ""
        ret += str(Book.lytex_header)
        for e in self.content:
            ret += e.latex_output()
        ret += str(Book.lytex_footer)
        return ret


def parse_cmd_options():
    global cmd_options
    parser = argparse.ArgumentParser()
    parser.add_argument('--in',   dest='in_path',  action='store', required=True)
    parser.add_argument('--out',  dest='out_path', action='store', required=True)
    parser.add_argument('--book', dest='book',     action='store', required=True)
    cmd_options = parser.parse_args()
    
    
def generate_lytex():
    os.makedirs(cmd_options.out_path, exist_ok=True)
    book_path = os.path.join(cmd_options.in_path, cmd_options.book + ".book")
    book = Book(book_path)
    lytex_path = os.path.join(cmd_options.out_path, cmd_options.book + ".lytex")
    with open(lytex_path, "w") as fd:
        fd.write(book.latex_output())


def generate_tex():
    # copy sty first, since lilypond-book tries to guess the textwidth
    shutil.copy(LIMETUSK_STY, cmd_options.out_path)

    cmd = ["lilypond-book", "--pdf", "--loglevel=WARN", "--lily-loglevel=WARN", "--format=latex",
           "--out="+cmd_options.out_path, os.path.join(cmd_options.out_path, cmd_options.book + ".lytex")]
    subprocess.call(cmd)


def compile_tex(draft=False):
    if draft:
        cmd = ["pdflatex", "-draftmode", "-output-directory=" + cmd_options.out_path, "-interaction=batchmode", cmd_options.book + ".tex"]
    else:
        cmd = ["pdflatex", "-output-directory=" + cmd_options.out_path, "-interaction=batchmode", cmd_options.book + ".tex"]
    temp_env = os.environ.copy()
    temp_env['TEXINPUTS'] = cmd_options.out_path + ":" + temp_env.get('TEXINPUTS', '')
    subprocess.call(cmd, env=temp_env)


def main():
    parse_cmd_options()
    print("Parsing book and converting songs...")
    generate_lytex()
    print("Generating book...")
    generate_tex()
    print("Compiling book...")
    print("Run 1...")
    compile_tex(draft=True)
    print("Run 2...")
    compile_tex(draft=True)
    print("Run 3...")
    compile_tex(draft=False)


if __name__ == "__main__":
    main()



