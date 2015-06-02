import subprocess
import logging
import os
import shutil
import limetusk.util


class BookBuilder(object):
    def __init__(self, book, options):
        self.book    = book
        self.options = options

    def build(self):
        logging.info("Generating book...")
        self.generate_lytex()

        logging.info("Compiling book...")
        self.generate_tex()
        self.compile_tex(draft=True)
        if not self.options.draft:
            self.compile_tex(draft=False)

    def generate_lytex(self):
        os.makedirs(self.options.out_path, exist_ok=True)
        lytex_path = os.path.join(self.options.out_path, self.book.title + ".lytex")
        with open(lytex_path, "w") as fd:
            fd.write(self.book.generate())

    def generate_tex(self):
        # copy sty first, since lilypond-book tries to guess the textwidth
        shutil.copy(limetusk.util.LIMETUSK_STY, self.options.out_path)
        cmd  = ["lilypond-book", "--pdf"]
        cmd += [] if self.options.verbose else ["--loglevel=WARN", "--lily-loglevel=WARN"]
        cmd += ["--format=latex"]
        cmd += ["--out="+self.options.out_path]
        cmd += [os.path.join(self.options.out_path, self.book.title + ".lytex")]
        subprocess.call(cmd)

    def compile_tex(self, draft=False):
        cmd  = ["pdflatex"]
        cmd += ["-draftmode"] if draft else []
        cmd += ["-interaction=nonstopmode"]
        cmd += ["-output-directory=" + self.options.out_path]
        cmd += [self.book.title + ".tex"]
        temp_env = os.environ.copy()
        temp_env['TEXINPUTS'] = self.options.out_path + ":" + temp_env.get('TEXINPUTS', '')
        if self.options.verbose == 2:
            subprocess.call(cmd, env=temp_env)
        else:
            subprocess.call(cmd, stdout=subprocess.DEVNULL, env=temp_env)
