import subprocess

LIMETUSK_STY = "bin/limetusk.sty"
TG2LY_BIN = "bin/tg2ly_0_3_1.jar"


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


def check_env():
    cmd  = ["lilypond-book", "--version"]
    try:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("lilypond-book not found!")
    cmd  = ["lilypond", "--version"]
    try:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("lilypond not found!")
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
