import os
import sys

from webob import Response

from zope.component import queryUtility
from zope.component.interfaces import ComponentLookupError
from zope.component import getSiteManager

from zope.interface import classProvides
from zope.interface import implements

from repoze.bfg.interfaces import ITemplateFactory
from repoze.bfg.interfaces import ITemplate
from repoze.bfg.interfaces import INodeTemplate

class Z3CPTTemplateFactory(object):
    classProvides(ITemplateFactory)
    implements(ITemplate)

    def __init__(self, path):
        from z3c.pt import PageTemplateFile
        self.template = PageTemplateFile(path)

    def __call__(self, **kw):
        result = self.template.render(**kw)
        return result

class XSLTemplateFactory(object):
    classProvides(ITemplateFactory)
    implements(INodeTemplate)

    def __init__(self, path):
        self.path = path

    def __call__(self, node, **kw):
        processor = get_processor(self.path)
        result = str(processor(node, **kw))
        return result

# Manage XSLT processors on a per-thread basis
import threading
from lxml import etree
xslt_pool = threading.local()
def get_processor(xslt_fn):
    try:
        return xslt_pool.processors[xslt_fn]
    except AttributeError:
        xslt_pool.processors = {}
    except KeyError:
        pass

    # Make a processor and add it to the pool
    source = etree.ElementTree(file=xslt_fn)
    proc = etree.XSLT(source)
    xslt_pool.processors[xslt_fn] = proc
    return proc

def package_path(package):
    return os.path.abspath(os.path.dirname(package.__file__))

def registerTemplate(type, template, path):
    try:
        sm = getSiteManager()
    except ComponentLookupError:
        pass
    else:
        sm.registerUtility(template, type, name=path)

def render_template(path, **kw):
    """ Render a z3c.pt (ZPT) template at the package-relative path
    (may also be absolute) using the kwargs in ``*kw`` as top-level
    names and return a string. """
    # XXX use pkg_resources
    path = caller_path(path)

    template = queryUtility(ITemplate, path)

    if template is None:
        if not os.path.exists(path):
            raise ValueError('Missing template file: %s' % path)
        template = Z3CPTTemplateFactory(path)
        registerTemplate(ITemplate, template, path)

    return template(**kw)

def render_template_to_response(path, **kw):
    """ Render a z3c.pt (ZPT) template at the package-relative path
    (may also be absolute) using the kwargs in ``*kw`` as top-level
    names and return a Response object. """
    path = caller_path(path)
    result = render_template(path, **kw)
    return Response(result)

def render_transform(path, node, **kw):
    """ Render a XSL template at the package-relative path (may also
    be absolute) using the kwargs in ``*kw`` as top-level names and
    return a string."""
    # Render using XSLT
    path = caller_path(path)

    template = queryUtility(INodeTemplate, path)
    if template is None:
        if not os.path.exists(path):
            raise ValueError('Missing template file: %s' % path)
        template = XSLTemplateFactory(path)
        registerTemplate(INodeTemplate, template, path)

    return template(node, **kw)

def render_transform_to_response(path, node, **kw):
    """ Render a XSL template at the package-relative path (may also
    be absolute) using the kwargs in ``*kw`` as top-level names and
    return a Response object."""
    path = caller_path(path)
    result = render_transform(path, node, **kw)
    return Response(result)

def caller_path(path):
    if not os.path.isabs(path):
        package_globals = sys._getframe(2).f_globals
        package_name = package_globals['__name__']
        package = sys.modules[package_name]
        prefix = package_path(package)
        path = os.path.join(prefix, path)
    return path

    
