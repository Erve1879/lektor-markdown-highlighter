from lektor.pluginsystem import Plugin
from lektor.context import get_ctx

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from markupsafe import Markup


class MarkdownHighlighterPlugin(Plugin):
    name = 'Markdown Highlighter'
    description = 'Adds syntax highlighting for markdown blocks.'

    def get_formatter(self, formatter_kwargs=None):
        """
        :param formatter_kwargs: Any keywords arguments to pass through to 
            ``pygments.formatters.HtmlFormatter``. Note that ``style`` will 
            be popped off the dictionary if passed.
        :type formatter_kwargs: dict
        """
        if not formatter_kwargs:
            # You can't .pop from None, so make sure we have a dict
            # (but don't set an empty dict to the kwarg's default value)
            formatter_kwargs = dict()
        formatter_kwargs.pop('style')
        return HtmlFormatter(style=self.get_style(), **formatter_kwargs)

    def get_style(self):
        return self.get_config().get('pygments.style', 'default')

    def highlight_code(self, text, lang):
        get_ctx().record_dependency(self.config_filename)
        lexer = get_lexer_by_name(lang)
        return highlight(text, lexer, self.get_formatter())

    def on_markdown_config(self, config, **extra):
        class HighlightMixin(object):
            def block_code(ren, text, lang):
                if not lang:
                    return super(HighlightMixin, ren).block_code(text, lang)
                return self.highlight_code(text, lang)
        config.renderer_mixins.append(HighlightMixin)

    def on_setup_env(self, **extra):
        def get_pygments_stylesheet(artifact_name='/static/pygments.css'):
            ctx = get_ctx()
            @ctx.sub_artifact(artifact_name=artifact_name, sources=[
                self.config_filename])
            def build_stylesheet(artifact):
                with artifact.open('w') as f:
                    f.write(self.get_formatter().get_style_defs())
            return artifact_name

        def pygmentize(text, lang):
            return Markup(self.highlight_code(text, lang))

        self.env.jinja_env.globals['get_pygments_stylesheet'] = \
            get_pygments_stylesheet
        self.env.jinja_env.filters['pygmentize'] = pygmentize
