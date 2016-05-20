from lektor.pluginsystem import Plugin
from lektor.context import get_ctx

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from markupsafe import Markup


class MarkdownHighlighterPlugin(Plugin):
    name = 'Markdown Highlighter'
    description = 'Adds syntax highlighting for markdown blocks.'

    def get_formatter(self, lang=None):
        """
        :param formatter_kwargs: Any keywords arguments to pass through to 
            ``pygments.formatters.HtmlFormatter``. Note that ``style`` will 
            be popped off the dictionary if passed.
        :type formatter_kwargs: dict
        """
        if lang:
            css = 'highlight ' + lang
        else:
            css = 'highlight'
        return HtmlFormatter(cssclass=css, **self.get_formatter_kwargs())

    def get_formatter_kwargs(self, lang=None):
        settings = self.get_config().to_dict()
        if not settings.get('pygments.style'):
            settings['pygments.style'] = 'default'
        formatter_kwargs = dict()
        for key, value in settings.items():
            new_key = key.replace('pygments.', '')
            formatter_kwargs[new_key] = value
        return formatter_kwargs

    def highlight_code(self, text, lang):
        get_ctx().record_dependency(self.config_filename)
        lexer = get_lexer_by_name(lang)
        return highlight(text, lexer, self.get_formatter(lang=lang))

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
