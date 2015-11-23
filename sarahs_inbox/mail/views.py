from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from urllib import unquote
from haystack.query import SearchQuerySet
from mail.models import *
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.cache import cache
import re


RESULTS_PER_PAGE = 50


def _search_string(request):
    return request.GET.get('q', None)
    

def _search_tokens(request):
    s = _search_string(request)
    if s is None:
        return []
        
    # protection!
    re_sanitize = re.compile(r'[^\w\d\s\'"\,\.\?\$]', re.I)
    s = re_sanitize.sub('', s)
    
    tokens = []
    re_quotes = re.compile(r'\"([^\"]+)\"')
    for m in re_quotes.findall(s):
        tokens.append(m.replace('"','').strip())        
        s = s.replace('"%s"' % m, '')
    for t in s.split(' '):
        tokens.append(t.strip())

    while '' in tokens:
        tokens.remove('')
        
    return tokens
    
    
def _highlight(text, tokens):
    regexes = []
    sorted_tokens = sorted(tokens, key=lambda x: len(x))
    for t in sorted_tokens:
        regexes.append(re.compile(r'(%s)' % t.replace(' ', r'\s+'), re.I))
    for r in regexes:
        text = r.sub('<span class="highlight">\\1</span>', text)
    return text


def _prepare_ids_from_cookie(request, cookie_name, method=None):
    if method == 'post':
        cookie = unquote(request.POST.get(cookie_name, '')).replace(',,', ',')
    else:
        cookie = unquote(request.COOKIES.get(cookie_name,'')).replace(',,', ',')
    print cookie
    if len(cookie)>1:
        if cookie[0]==',':
            cookie = cookie[1:]
        if cookie[-1]==',':
            cookie = cookie[:-1]
    
    try:
        id_list = map(lambda x: (x!='') and int(x) or 0, cookie.split(','))
    except:
        id_list = []

    return id_list
    
    
def _annotate_emails(emails, search=[]):
    r = []
    for email in emails:
        email.text = _highlight(email.text, search)
        r.append({ 'creator_html': email.creator_html(), 'to_html': email.to_html(), 'cc_html': email.cc_html(), 'obj': email })
    return r


def index(request, search=[], threads=None):
    
    if threads is None:
        palin = Person.objects.sarah_palin()
        threads = Thread.objects.exclude(creator__in=palin).order_by('-date')

    threads_count = threads.count()
        
    p = Paginator(threads, RESULTS_PER_PAGE)
    
    page_num = 1
    try:
        page_num = int(request.GET.get('page', 1))
    except:
        pass
    page = p.page(page_num)

    highlighted_threads = []
    for thread in page.object_list:
        if (threads is not None) and type(threads) is SearchQuerySet: # deal with searchqueryset objects
            thread = thread.object

        thread.name = _highlight(thread.name, search)
        highlighted_threads.append(thread)
            
    template_vars = {
        'range': "<strong>%d</strong> - <strong>%d</strong> of <strong>%d</strong>" % (page.start_index(), page.end_index(), threads_count),
        'num_pages': p.num_pages , 
        'next': page_num<p.num_pages and min(p.num_pages,page_num+1) or False, 
        'prev': page_num>1 and max(1, page_num-1) or False, 
        'first': '1', 
        'last': p.num_pages, 
        'current_page': page_num, 
        'threads': highlighted_threads, 
        'search': " ".join(search), 
        'search_orig': (_search_string(request) is not None) and _search_string(request) or '', 
        'path': request.path,
    }
    
    return render_to_response('index.html', template_vars, context_instance=RequestContext(request))

def sent(request):
    kagan = Person.objects.elena_kagan()
    emails = Thread.objects.filter(creator=kagan).order_by('-date')
    return index(request, threads=emails)

def contact_by_id(request, contact_id, suppress_redirect=False):
    cache_key = 'contact_%d' % int(contact_id)
    threads = cache.get(cache_key)
    if threads is None:        
        try:
            person = Person.objects.get(id=contact_id)
        except Person.DoesNotExist, e:
            return HttpResponseRedirect(reverse('mail.views.index'))
    
        if person.merged_into is not None:
            return HttpResponseRedirect('/contact/%d/' % person.merged_into.id)
    
        threads = []
        emails = Email.objects.filter(Q(to=person)|Q(cc=person))
        for e in emails:
            if e.email_thread is not None:
                threads.append(e.email_thread.id)
        threads = Thread.objects.filter(id__in=threads).order_by('-date')
        
        cache.set(cache_key, threads)
    
    return index(request, threads=threads)

def contact_by_name(request, contact_name):
    try:
        contact = Person.objects.get(slug=contact_name)
    except Person.DoesNotExist, e:
        return HttpResponseRedirect(reverse('mail.views.contacts_index'))
    except Thread.MultipleObjectsReturned, e:
        return HttpResponseRedirect(reverse('mail.views.contacts_index'))
    
    return contact_by_id(request, contact.id, suppress_redirect=True)
    
def contacts_index(request):
    return index(request)


def thread_by_id(request, thread_id, suppress_redirect=False):
    try:
        thread = Thread.objects.get(id=thread_id)
    except Thread.DoesNotExist, e:
        return HttpResponseRedirect(reverse('mail.views.index'))

    # if merged thread, redirect
    if thread.merged_into is not None:
        return HttpResponseRedirect('/thread/%d/' % thread.merged_into.id)

    # if access by ID, redirect to descriptive URL
    if (not suppress_redirect) and (len(thread.slug.strip())>3):
        return HttpResponseRedirect('/thread/%s/' % thread.slug)

    search = _search_tokens(request)
    thread_starred = thread.id in _prepare_ids_from_cookie(request, 'kagan_star')
    emails = _annotate_emails(Email.objects.filter(email_thread=thread).order_by('creation_date_time'), search)    

    return render_to_response('thread.html', {'thread': thread, 'thread_starred': thread_starred, 'emails': emails }, context_instance=RequestContext(request))

def thread_by_name(request, thread_name):
    try:
        thread = Thread.objects.get(slug=thread_name)
    except Thread.DoesNotExist, e:
        return HttpResponseRedirect(reverse('mail.views.index'))
    except Thread.MultipleObjectsReturned, e:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    return thread_by_id(request, thread.id, suppress_redirect=True)

    
def search(request):
    tokens = _search_tokens(request)
    if len(tokens) is None:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    sqs = SearchQuerySet().models(Thread)
    for t in tokens:
        sqs = sqs.filter_or(text_and_recipients=t)
    sqs = sqs.order_by('-date')

    if sqs.count()==0:
        return render_to_response('search_empty.html', { 'path': request.path }, context_instance=RequestContext(request))

    return index(request, search=tokens, threads=sqs)


def star_record_ajax(request, thread_id, action):
    try:
        thread = Thread.objects.get(id=thread_id)
    except Thread.DoesNotExist, e:
        return HttpResponse('{ status: \'not_found\'}');
    
    if thread.star_count is None:
        thread.star_count = 0
    if action=='add':
        thread.star_count += 1
    elif action=='remove':
        thread.star_count -= 1
    thread.save()

    return HttpResponse('{ status: \'success\'}')


def starred(request):
    if not request.POST.get('kagan_star'):
        return HttpResponseRedirect(reverse('mail.views.index'))

    starred_ids = _prepare_ids_from_cookie(request, 'kagan_star', method='post')
    if len(starred_ids)==0:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    starred = Thread.objects.filter(id__in=starred_ids).order_by('-date')

    if starred.count()==0:
        return render_to_response('search_empty.html', { 'path': request.path }, context_instance=RequestContext(request))
    else:
        return index(request, threads=starred)

    return index(request, threads=starred)
    

def starred_all(request):
    starred = Thread.objects.filter(star_count__gt=0).order_by('-star_count','-date')
    if starred.count()==0:
        return render_to_response('search_empty.html', { 'path': request.path }, context_instance=RequestContext(request))
    else:
        return index(request, threads=starred)
