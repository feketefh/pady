from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, path: str = None):
        super().__init__(document)
        self.highlighting_rules = []
        self.triple_single = re.compile(r"'''")
        self.triple_double = re.compile(r'"""')
        self.multi_line_string_format = QTextCharFormat()
        self.multi_line_string_format.setForeground(QColor("#cf723d"))
        if path and path.endswith(".py"):
            self.setupPythonHighlighting()

    def setupPythonHighlighting(self):
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c486c1"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del", "elif",
            "else", "except", "False", "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise",
            "return", "True", "try", "while", "with", "yield"
        ]
        keyword_pattern = re.compile(r'\b(' + '|'.join(keywords) + r')\b')
        self.highlighting_rules.append((keyword_pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#cf723d"))
        string_pattern = re.compile(r'("([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\')')
        self.highlighting_rules.append((string_pattern, string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGreen"))
        comment_format.setFontItalic(True)
        comment_pattern = re.compile(r'#.*')
        self.highlighting_rules.append((comment_pattern, comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#6897bb"))
        number_pattern = re.compile(r'\b\d+(\.\d+)?\b')
        self.highlighting_rules.append((number_pattern, number_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#b58900"))
        decorator_pattern = re.compile(r'@\w+')
        self.highlighting_rules.append((decorator_pattern, decorator_format))

        funcdef_format = QTextCharFormat()
        funcdef_format.setForeground(QColor("#61afef"))
        funcdef_format.setFontWeight(QFont.Weight.Bold)
        funcdef_pattern = re.compile(r'\bdef\s+([A-Za-z_][A-Za-z0-9_]*)')
        self.highlighting_rules.append((funcdef_pattern, funcdef_format))

        classdef_format = QTextCharFormat()
        classdef_format.setForeground(QColor("#e5c07b"))
        classdef_format.setFontWeight(QFont.Weight.Bold)
        classdef_pattern = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
        self.highlighting_rules.append((classdef_pattern, classdef_format))

    def highlightBlock(self, text):
        self.setCurrentBlockState(0)
        in_multiline = self.match_multiline(text, self.triple_single, self.multi_line_string_format, 1)
        if not in_multiline:
            in_multiline = self.match_multiline(text, self.triple_double, self.multi_line_string_format, 2)

        if not in_multiline:
            for pattern, fmt in self.highlighting_rules:
                for match in pattern.finditer(text):
                    start, end = match.span()
                    self.setFormat(start, end - start, fmt)

    def match_multiline(self, text, delimiter, fmt, state):
        start = 0
        if self.previousBlockState() == state:
            match = delimiter.search(text)
            if match:
                end = match.end()
                self.setFormat(0, end, fmt)
                self.setCurrentBlockState(0)
                return False
            else:
                self.setFormat(0, len(text), fmt)
                self.setCurrentBlockState(state)
                return True
        match = delimiter.search(text)
        if match:
            start = match.start()
            match2 = delimiter.search(text, match.end())
            if match2:
                end = match2.end()
                self.setFormat(start, end - start, fmt)
                return False
            else:
                self.setFormat(start, len(text) - start, fmt)
                self.setCurrentBlockState(state)
                return True
        return False
