import os.path
from repoze.bfg.template import render_template_to_response

class pushpage(object):
    """ Decorator for functions which return ZPT template namespaces.

    E.g.::

      @pushpage('www/my_template.pt')
      def my_view(context, request):
          return {'a': 1, 'b': ()}

    Equates to::

      def my_view(context, request):
          return render_template('www/my_template.pt', a=1, b=())
        
    """
    def __init__(self, template):
        self.template = template

    def __call__(self, wrapped):
        prefix = os.path.dirname(wrapped.func_globals['__file__'])
        path = os.path.join(prefix, self.template)

        def _curried(context, request):
            kw = wrapped(context, request)
            return render_template_to_response(path, **kw)
        _curried.__name__ = wrapped.__name__

        return _curried
