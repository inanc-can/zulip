#!/usr/bin/env python

"""
Fenced Code Extension for Python Markdown
=========================================

This extension adds Fenced Code Blocks to Python-Markdown.

    >>> import markdown
    >>> text = '''
    ... A paragraph before a fenced code block:
    ...
    ... ~~~
    ... Fenced code block
    ... ~~~
    ... '''
    >>> html = markdown.markdown(text, extensions=['fenced_code'])
    >>> print html
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Works with safe_mode also (we check this because we are using the HtmlStash):

    >>> print markdown.markdown(text, extensions=['fenced_code'], safe_mode='replace')
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Include tilde's in a code block and wrap with blank lines:

    >>> text = '''
    ... ~~~~~~~~
    ...
    ... ~~~~
    ... ~~~~~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code>
    ~~~~
    </code></pre>

Language tags:

    >>> text = '''
    ... ~~~~{.python}
    ... # Some python code
    ... ~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code class="python"># Some python code
    </code></pre>

Copyright 2007-2008 [Waylan Limberg](http://achinghead.com/).

Project website: <http://packages.python.org/Markdown/extensions/fenced_code_blocks.html>
Contact: markdown@freewisdom.org

License: BSD (see ../docs/LICENSE for details)

Dependencies:
* [Python 2.4+](http://python.org)
* [Markdown 2.0+](http://packages.python.org/Markdown/)
* [Pygments (optional)](http://pygments.org)

"""

import re
import markdown
from zerver.lib.bugdown.codehilite import CodeHilite, CodeHiliteExtension

# Global vars
FENCE_RE = re.compile(r'(?P<fence>^(?:~{3,}|`{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)$', re.MULTILINE|re.DOTALL)
FENCED_BLOCK_RE = re.compile( \
    r'(?P<fence>^(?:~{3,}|`{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)?[ ]*\n(?P<code>.*?)(?<=\n)(?P=fence)[ ]*$',
    re.MULTILINE|re.DOTALL
    )
CODE_WRAP = '<pre><code%s>%s</code></pre>'
LANG_TAG = ' class="%s"'

class FencedCodeExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        # Newer versions of Python-Markdown (starting at 2.3?) have
        # a normalize_whitespace preprocessor that needs to go first.
        position = ('>normalize_whitespace'
            if 'normalize_whitespace' in md.preprocessors
            else '_begin')

        md.preprocessors.add('fenced_code_block',
                                 FencedBlockPreprocessor(md),
                                 position)


class FencedBlockPreprocessor(markdown.preprocessors.Preprocessor):

    def __init__(self, md):
        markdown.preprocessors.Preprocessor.__init__(self, md)

        self.checked_for_codehilite = False
        self.codehilite_conf = {}

    def format_code(self, langclass, lang, text):
        # Check for code hilite extension
        if not self.checked_for_codehilite:
            for ext in self.markdown.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.config
                    break

            self.checked_for_codehilite = True

        # If config is not empty, then the codehighlite extension
        # is enabled, so we call it to highlite the code
        if self.codehilite_conf:
            highliter = CodeHilite(text,
                    force_linenos=self.codehilite_conf['force_linenos'][0],
                    guess_lang=self.codehilite_conf['guess_lang'][0],
                    css_class=self.codehilite_conf['css_class'][0],
                    style=self.codehilite_conf['pygments_style'][0],
                    lang=(lang or None),
                    noclasses=self.codehilite_conf['noclasses'][0])

            code = highliter.hilite()
        else:
            code = CODE_WRAP % (langclass, self._escape(text))

        return code

    def format_quote(self, text):
        paragraphs = text.split("\n\n")
        quoted_paragraphs = []
        for paragraph in paragraphs:
            lines = paragraph.split("\n")
            quoted_paragraphs.append("\n".join("> " + line for line in lines if line != ''))
        return "\n\n".join(quoted_paragraphs)

    def format_fence(self, m):
        langclass = ''
        if m.group('lang'):
            langclass = LANG_TAG % m.group('lang')
            if m.group('lang') in ('quote', 'quoted'):
                replacement = self.format_quote(m.group('code'))
                return replacement

        code = self.format_code(langclass, m.group('lang'), m.group('code'))
        placeholder = self.markdown.htmlStash.store(code, safe=True)
        return placeholder

    def process_fence(self, m, text):
        fence_text = self.format_fence(m)
        return '%s\n%s\n%s'% (text[:m.start()], fence_text, text[m.end():])

    def run(self, lines):
        """ Match and store Fenced Code Blocks in the HtmlStash. """

        text = "\n".join(lines)
        while 1:
            m = FENCED_BLOCK_RE.search(text)
            if m:
                text = self.process_fence(m, text)
            else:
                break


        fence = FENCE_RE.search(text)
        if fence:
            # If we found a starting fence but no ending fence,
            # then we add a closing fence before the two newlines that
            # markdown automatically inserts
            if text[-2:] == '\n\n':
                text = text[:-2] + '\n' + fence.group('fence') + text[-2:]
            else:
                text += fence.group('fence')
            m = FENCED_BLOCK_RE.search(text)
            if m:
                text = self.process_fence(m, text)

        return text.split("\n")

    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(configs=None):
    return FencedCodeExtension(configs=configs)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
