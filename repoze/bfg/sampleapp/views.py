import formencode
import time

from webob.exc import HTTPFound

from repoze.bfg.template import render_template_to_response
from repoze.bfg.sampleapp.models import BlogEntry
from repoze.bfg.security import has_permission

def datestring(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def blog_default_view(context, request):
    entrydata = []

    can_add = False
    if has_permission('add', context, request):
        can_add = True
    for name, entry in context.items():
        entrydata.append(
            {
            'name':name,
            'title':entry.title,
            'author':entry.author,
            'created':datestring(entry.created),
            'message':request.params.get('message'),
            }
            )

    return render_template_to_response('templates/blog.pt',
                                       name=context.__name__,
                                       entries=entrydata,
                                       can_add=can_add)

def blog_entry_default_view(context, request):
    info = {
        'name':context.__name__,
        'title':context.title,
        'body':context.body,
        'author':context.author,
        'created':datestring(context.created),
        }
    return render_template_to_response('templates/blog_entry.pt', **info)

class BlogAddSchema(formencode.Schema):
    allow_extra_fields = True
    author = formencode.validators.NotEmpty()
    body = formencode.validators.NotEmpty()
    title = formencode.validators.NotEmpty()

def blog_entry_add_view(context, request):
    params = request.params

    message = None
    
    author = params.get('author', '')
    body = params.get('body', '')
    title = params.get('title', '')
    info = dict(request=request, author=author, body=body, title=title,
                message=None)

    if params.has_key('form.submitted'):
        schema = BlogAddSchema()
        try:
            form = schema.to_python(params)
        except formencode.validators.Invalid, why:
            message = str(why)
            info['message'] = message
        else:
            author, body, title = form['author'], form['body'], form['title']
            new_entry = BlogEntry(title, body, author)
            name = str(time.time())
            context[name] = new_entry
            return HTTPFound(location='/')

    return render_template_to_response('templates/blog_entry_add.pt', **info)
                      
def contents_view(context, request):
    return render_template_to_response('templates/contents.pt', context=context)
