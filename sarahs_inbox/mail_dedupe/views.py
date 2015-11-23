from settings import *
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from urllib import unquote
from mail.models import *
from django.core.urlresolvers import reverse
from django.core.cache import cache
import re
import jellyfish
from mail.management.commands.mail_combine_people import Command as CombineCommand

def index(request):
    
    if not DEBUG:
        return
    
    DEFAULT_DISTANCE = 0
        
    person_into = request.GET.get('into', False)
    victims = map(lambda x: int(x), request.GET.getlist('combine'))
    if person_into is not False:
        victims.remove(int(person_into))
        args_array = [person_into] + victims
        # call_command('mail_combine_people', *args_array)
        combcomm = CombineCommand()
        print person_into, victims
        result = combcomm.merge(person_into, victims, noprint=True)
    
    
    people = []
    for p in Person.objects.filter(merged_into=None).order_by('name_hash'):
        people.append({'obj': p, 'dist': DEFAULT_DISTANCE})
    
    target_person = None
    target_id = request.GET.get('id', False)
    if target_id is not False:
        target_person = Person.objects.get(id=target_id)
    
        if target_person:
            for (i,p) in enumerate(people):
                people[i]['dist'] = jellyfish.jaro_distance(target_person.name_hash, p['obj'].name_hash)
            people.sort(key=lambda x: x['dist'], reverse=True)
    
    total = len(people)
    
    template_vars = {
        'people': people,
        'total': total
    }
    
    return render_to_response('dedupe.html', template_vars, context_instance=RequestContext(request))
    
def emails(request):    
    person = Person.objects.get(id=request.GET.get('id'))
    
    from_emails = Email.objects.filter(creator=person)
    to_emails = Email.objects.filter(to=person)
    cc_emails = Email.objects.filter(cc=person)
    
    template_vars = {
        'from_emails': from_emails,
        'to_emails': to_emails,
        'cc_emails': cc_emails
    }
    
    return render_to_response('dedupe_emails.html', template_vars, context_instance=RequestContext(request))
    
    
    
    