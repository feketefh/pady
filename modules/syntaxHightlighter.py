import os
import json
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, path: str=None):
        super().__init__(document)
        self.path = path
        self.language = self.get_language_from_path(path)
        self.colors = self.load_colors()
        self.highlighting_rules = []
        self.setup_highlighting()

    def get_language_from_path(self, path):
        if not path:
            return "python"
        ext = os.path.splitext(path)[1].lower()
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "c++",
            ".cc": "c++",
            ".cxx": "c++",
            ".hpp": "c++",
            ".h": "c++",
            ".cs": "c#",
            ".html": "html",
            ".htm": "html",
            ".css": "css"
        }
        return ext_map.get(ext, "python")  # fallback to python

    def load_colors(self):
        json_path = os.path.join(os.path.dirname(__file__), "syntax_colors.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                color_data = json.load(f)
            return color_data.get(self.language, color_data["python"])
        except Exception:
            return {
                "keyword": "#c678dd",
                "string": "#98c379",
                "comment": "#5c6370",
                "number": "#d19a66",
                "function": "#61afef",
                "class": "#e5c07b",
                "decorator": "#b58900"
            }

    def setup_highlighting(self):
        path = self.path

        if path and path.endswith(".py"):
            keywords = [
                "and", "as", "assert", "break", "class", "continue", "def", "del", "elif",
                "else", "except", "False", "finally", "for", "from", "global", "if", "import",
                "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise",
                "return", "True", "try", "while", "with", "yield"
            ]
            self.add_keyword_rules(keywords)
            self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', "string")
            self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", "string")
            self.add_rule(r'#.*', "comment", italic=True)
            self.add_rule(r'\b\d+(\.\d+)?\b', "number")
            self.add_rule(r'\bdef\s+([A-Za-z_][A-Za-z0-9_]*)', "function", bold=True)
            self.add_rule(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', "class", bold=True)
            self.add_rule(r'@\w+', "decorator")

        elif path and path.endswith((".js", ".ts")):
            keywords = [
                "break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete",
                "do", "else", "export", "extends", "finally", "for", "function", "if", "import", "in",
                "instanceof", "let", "new", "return", "super", "switch", "this", "throw", "try", "typeof",
                "var", "void", "while", "with", "yield", "enum", "implements", "interface", "package", "private",
                "protected", "public", "static", "await", "async"
            ]
            self.add_keyword_rules(keywords)
            self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', "string")
            self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", "string")
            self.add_rule(r'`[^`\\]*(\\.[^`\\]*)*`', "string")
            self.add_rule(r'//.*', "comment", italic=True)
            self.add_rule(r'/\*[\s\S]*?\*/', "comment", italic=True)
            self.add_rule(r'\b\d+(\.\d+)?\b', "number")
            self.add_rule(r'\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)', "function", bold=True)
            self.add_rule(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', "class", bold=True)

        elif path and path.endswith(".java"):
            keywords = [
                "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
                "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
                "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
                "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp",
                "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void",
                "volatile", "while", "true", "false", "null"
            ]
            self.add_keyword_rules(keywords)
            self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', "string")
            self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", "string")
            self.add_rule(r'//.*', "comment", italic=True)
            self.add_rule(r'/\*[\s\S]*?\*/', "comment", italic=True)
            self.add_rule(r'\b\d+(\.\d+)?\b', "number")
            self.add_rule(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', "class", bold=True)
            self.add_rule(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', "function")

        elif path and path.endswith((".cpp", ".h", ".c", ".hpp", ".cc", ".cxx")):
            keywords = [

                "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break", "case",
                "catch", "char", "char16_t", "char32_t", "class", "compl", "const", "constexpr", "const_cast",
                "continue", "decltype", "default", "delete", "do", "double", "dynamic_cast", "else", "enum",
                "explicit", "export", "extern", "false", "float", "for", "friend", "goto", "if", "inline", "int",
                "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or",
                "or_eq", "private", "protected", "public", "register", "reinterpret_cast", "return", "short",
                "signed", "sizeof", "static", "static_assert", "static_cast", "struct", "switch", "template",
                "this", "thread_local", "throw", "true", "try", "typedef", "typeid", "typename", "union",
                "unsigned", "using", "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",

                "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char", "checked", "class",
                "const", "continue", "decimal", "default", "delegate", "do", "double", "else", "enum", "event",
                "explicit", "extern", "false", "finally", "fixed", "float", "for", "foreach", "goto", "if",
                "implicit", "in", "int", "interface", "internal", "is", "lock", "long", "namespace", "new",
                "null", "object", "operator", "out", "override", "params", "private", "protected", "public",
                "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof", "stackalloc", "static",
                "string", "struct", "switch", "this", "throw", "true", "try", "typeof", "uint", "ulong",
                "unchecked", "unsafe", "ushort", "using", "virtual", "void", "volatile", "while"
            ]
            self.add_keyword_rules(keywords)
            self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', "string")
            self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", "string")
            self.add_rule(r'//.*', "comment", italic=True)
            self.add_rule(r'/\*[\s\S]*?\*/', "comment", italic=True)
            self.add_rule(r'\b\d+(\.\d+)?\b', "number")
            self.add_rule(r'\bclass\s+([A-Za-z_][A-ZaZ0-9_]*)', "class", bold=True)
            self.add_rule(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', "function")

        elif path and path.endswith(".html"):
            tag_format = QTextCharFormat()
            tag_format.setForeground(QColor(self.colors.get("tag", "#22863a")))
            tag_format.setFontWeight(QFont.Weight.Bold)
            self.highlighting_rules.append((QRegularExpression(r'</?[a-zA-Z][a-zA-Z0-9]*'), tag_format))

            attr_format = QTextCharFormat()
            attr_format.setForeground(QColor(self.colors.get("attribute", "#6f42c1")))
            self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z-:]+(?=\=)'), attr_format))

            self.add_rule(r'"[^"]*"', "string")
            self.add_rule(r"'[^']*'", "string")
            self.add_rule(r'<!--[\s\S]*?-->', "comment", italic=True)

        elif path and path.endswith(".css"):

            selector_format = QTextCharFormat()
            selector_format.setForeground(QColor(self.colors.get("selector", "#22863a")))
            selector_format.setFontWeight(QFont.Weight.Bold)
            self.highlighting_rules.append((QRegularExpression(r'^[\.\#]?[a-zA-Z0-9\-\_]+(?=\s*\{)'), selector_format))

            property_format = QTextCharFormat()
            property_format.setForeground(QColor(self.colors.get("property", "#005cc5")))
            self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z\-]+(?=\s*:)'), property_format))

            self.add_rule(r'"[^"]*"', "string")
            self.add_rule(r"'[^']*'", "string")
            self.add_rule(r'\b\d+(\.\d+)?\b', "number")

            self.add_rule(r'/\*[\s\S]*?\*/', "comment", italic=True)

    def add_keyword_rules(self, keywords):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.colors["keyword"]))
        fmt.setFontWeight(QFont.Weight.Bold)
        for word in keywords:
            pattern = QRegularExpression(rf'\b{word}\b')
            self.highlighting_rules.append((pattern, fmt))

    def add_rule(self, pattern, color_key, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.colors.get(color_key, "#000000")))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(pattern), fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
