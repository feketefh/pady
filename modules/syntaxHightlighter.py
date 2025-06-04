from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, path:str):
        super().__init__(document)
        self.highlighting_rules = []

        path = "dog" if path == None else path
        if path.endswith(".py"):
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

        self.highlighting_rules = [(re.compile(rf'\b{word}\b'), keyword_format) for word in keywords]

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#cf723d"))
        self.highlighting_rules.append((re.compile(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'[^']*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGreen"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'#.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)
