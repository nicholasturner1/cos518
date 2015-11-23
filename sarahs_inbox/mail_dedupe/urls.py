from django.views.generic.simple import direct_to_template, redirect_to
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^dedupe/$', 'mail_dedupe.views.index', name='dedupe'),
    url(r'^dedupe/mail/', 'mail_dedupe.views.emails', name='dedupe_mail'),
)