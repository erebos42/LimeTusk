import os.path
import ast
import subprocess
import logging
import limetusk.util
from limetusk.util import escape_latex


class InvalidBookElementError(Exception):
    pass

class BookElement(object):
    def generate(self):
        raise NotImplementedError("please implement!")

    @classmethod
    def get_keyword(self):
        raise NotImplementedError("please implement!")

    @classmethod
    def _eval_file(cls, path):
        # TODO: what if file does not exist?!
        with open(path, 'r') as fd:
            try:
                return ast.literal_eval(fd.read().strip())
            except SyntaxError:
                raise InvalidBookElementError

    @classmethod
    def factory(cls, base_path, options, object_str, init_data):
        for e in BookElement.__subclasses__():
            if e.get_keyword() == object_str:
                return e(base_path, options, init_data)
        raise InvalidBookElementError("keyword not found")

class Chapter(BookElement):
    str_template = r"""
        \ltchapter{{{chapter_name}}}
    """

    def __init__(self, base_path, options, init_data):
        self.text = init_data
        super().__init__()

    def __str__(self):
        return "Chapter: {}".format(self.text)

    @classmethod
    def get_keyword(self):
        return "chapter"

    def generate(self):
        return self.str_template.format(chapter_name=self.text)


class Song(BookElement):
    # TODO: this should not be two templates. But the trailing % of the songheader is kind of annoying...
    str_template = r"""
        \songheader{{{title}}}{{{artist}}}{{{album}}}{{{tuning}}}{{{composer}}}
        \lilypondfile{{{path}}}
    """
    
    str_midi_template = r"""
        \songheader{{{title}}}{{{artist}}}{{{album}}}{{{tuning}}}{{{composer}}}%
        \marginpar{{\attachfile[mimetype=audio/midi, print=false]{{{midi_file}}}}}
        \lilypondfile{{{path}}}
    """

    default = {"artist": "",
               "title": "",
               "album": "",
               "tuning": "",
               "composer": "",
               "tg_file": ""}

    def __init__(self, base_path, options, init_path):
        init_data = BookElement._eval_file(os.path.join(base_path, init_path))
        self.options = options
        
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
        self.data["tg_file"] = os.path.join(base_path, self.data["tg_file"])
        if not os.path.exists(self.data["tg_file"]):
            raise FileNotFoundError
        super().__init__()

    def __str__(self):
        return "Song: {}".format(self.data["title"])

    @classmethod
    def get_keyword(self):
        return "song"

    def generate(self):
        self.data["hash"] = self.convert()
        if self.options.midi:
            self.generate_midi()

        if self.options.midi:
            template = self.str_midi_template
        else:
            template = self.str_template
    
        return template.format(artist    = escape_latex(self.data["artist"]),
                                title     = escape_latex(self.data["title"]),
                                tuning    = escape_latex(self.data["tuning"]),
                                album     = escape_latex(self.data["album"]),
                                composer  = escape_latex(self.data["composer"]),
                                midi_file = os.path.join(self.options.out_path, self.data["hash"] + ".midi"),
                                path      = os.path.join(self.options.out_path, self.data["hash"] + ".ly"))


    def generate_midi(self):
        """Make and change copy of .ly-file for midi generation. This is necessary,
        because lilypond-book has this crazy naming scheme, so there is basically
        no way of finding the generated midi files. So we insert the \midi-block
        by hand and compile only for the midi file again.
        """
        rel_path  = os.path.join(self.options.out_path, self.data["hash"])
        ly_path   = rel_path + ".ly"
        m_ly_path = rel_path + "_midi.ly"
        with open(ly_path, "r") as fd_r, open(m_ly_path, "w") as fd_w:
            ly_data = fd_r.read().replace("% __MAGIC_MIDI_VS_LAYOUT_MARKER__", "\\midi {}")
            fd_w.write(ly_data)
        cmd  = ["lilypond"]
        cmd += [] if not self.options.verbose < 2 else ["--loglevel=NONE"]
        cmd += ["-o", rel_path, m_ly_path]
        out = subprocess.check_output(cmd)
        os.remove(m_ly_path)

    def convert(self):
        cmd = ["java", "-jar", limetusk.util.TG2LY_BIN, "--in", self.data["tg_file"], "--out", self.options.out_path]
        out = subprocess.check_output(cmd)
        out = out.decode('utf-8').replace('\n', '')
        return out


class CSong(BookElement):
    str_template = r"""
        \csongtoc{{{title}}}{{{artist}}}
        \beginsong{{{title}}}[
          by={{{artist}}},
          cr={{{composer}}},
        ]
            \musicnote{{{tuning}}}
        
            {content}
        \endsong
    """
    
    default = {"artist": "",
               "title": "",
               "tuning": "",
               "composer": "",
               "album": "",
               "year": "",
               "content": ""}

    def __init__(self, base_path, options, init_path):
        init_data = BookElement._eval_file(os.path.join(base_path, init_path))
        
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
        super().__init__()

    def __str__(self):
        return "CSong: {}".format(self.data["title"])

    @classmethod
    def get_keyword(self):
        return "csong"

    @classmethod
    def begin_env(self):
        return r"""\begin{songs}{}
                """

    @classmethod
    def end_env(self):
        return r"""\end{songs}
                """

    def generate(self):
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

    def __init__(self, base_path, options, init_path):
        init_data = BookElement._eval_file(os.path.join(base_path, init_path))
        
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
        super().__init__()

    def __str__(self):
        return "Quote: {}".format(self.data["source"])

    @classmethod
    def get_keyword(self):
        return "quote"

    def generate(self):
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

    def __init__(self, base_path, options, init_path):
        init_data = BookElement._eval_file(os.path.join(base_path, init_path))
        
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
        self.data["pic_path"] = os.path.join(base_path, self.data["pic_path"])
        self.data["pic_path"] = os.path.abspath(self.data["pic_path"])
        super().__init__()

    def __str__(self):
        return "Picture: {}".format(self.data["pic_path"])

    @classmethod
    def get_keyword(self):
        return "pic"

    def generate(self):
        return Picture.str_template.format(align=self.data["align"], size=self.data["size"], path=self.data["pic_path"])


class Title(BookElement):
    def __init__(self, base_path, options, init_data):
        self.title = init_data
        super().__init__()

    def __str__(self):
        return "Title: {}".format(self.title)

    @classmethod
    def get_keyword(self):
        return "title"

    def generate(self):
        return ""
