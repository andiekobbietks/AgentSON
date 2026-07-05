"""Applies the amber-phosphor theme override to the adr-viewer generated
output. Run after `adr-viewer` generates docs/standards/adr-index.html.

Kept as a real script file rather than an inline `run:` block in the
workflow YAML, because YAML block-scalar indentation gets passed through
literally to any inline heredoc/`-c` string, which breaks Python's
top-level indentation rules.
"""
import sys

TARGET = "docs/standards/adr-index.html"
THEME = ".github/workflows/adr-viewer-theme.html"


def main() -> int:
    content = open(TARGET, encoding="utf-8").read()
    theme_block = open(THEME, encoding="utf-8").read()

    if content.count("</head>") != 1:
        print(f"ERROR: expected exactly one </head> in {TARGET}, found {content.count('</head>')}")
        return 1

    content = content.replace("</head>", theme_block)
    open(TARGET, "w", encoding="utf-8").write(content)
    print(f"Applied theme to {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
