#!/usr/bin/env python

__doc__ = '''
Gmail Parsing Script for COS518

ORDER OF OPERATIONS
-Read files from the downloaded mbox file
-Extract fields of interest (tag fields, defined below)
-Passes to email_parser module for natural language processing
'''

import email_parser
import email_io

#Python dependencies
import mailbox
import base64
import argparse

email_tags = ["From","To","Date","Subject"]
#=====================================================================
#HTML removal solution from StackOverflow (fingers crossed...)
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self,d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    try:
        s.feed(html)
    except:
        return html
    return s.get_data()

#=====================================================================
#Gmail mbox Preprocessing Functions

def open_mbox(input_filename):
    '''Serves both reading and writing'''
    return mailbox.mbox(input_filename)

def num_emails(input_filename):
    '''Returns the number of emails in an mbox file'''
    return len( open_mbox(input_filename) )

def filter_emails(mbox):
    '''
    Returns a list of mailbox messages which exclude
    the messages satisfying any criteria below
    NOTE: this is slightly different from a full mailbox.mbox
     but this allows us to avoid duplicating the (large)
     mbox file on disk
    '''

    new_mbox = []

    for i in range(len(mbox)):
        print "Filtering Email: # %d of %d" % (i, len(mbox))
        message = mbox[i]

        if in_field("Chat",'X-Gmail-Labels',message):
            continue

        if in_field("Calendar",'From',message):
            continue

        if in_field("html",'Content-Type',message):
            continue

        new_mbox.append( message )

    return new_mbox

        
def in_field(text, field, message):
    '''Extracts a field and avoids errors'''
    return (message.has_key(field) and text in message[field])


def read_main_mail(message):
    '''Extracts the message body from an email message'''

    message_layer = message
    while message_layer.is_multipart():
        message_layer = message_layer.get_payload()[0]
   
    result = message_layer.get_payload()

    if message_layer['Content-Transfer-Encoding'] == 'base64':
        result = base64.b64decode(result)

    return result


def pretty_print(message):
    '''Useful for debugging'''

    print message['From']
    print message['Date']

    print strip_tags(str(read_main_mail(message)))


def extract_email_tags(message, key):
    '''Extracts the fields defined above (email_tags) from the email datatype'''
    
    tags = {}
    tags["key"] = str(key)
    
    for tag in email_tags:
        tags[tag] = message[tag].replace('\n','') if message.has_key(tag) else ""

    return tags


def extract_all_email_tags(mbox):
    '''Applies the above over an mbox object'''
    
    email_tags = []
    for i in range(len(mbox)):
        email_tags.append( extract_email_tags(mbox[i], i) )

    return email_tags



def extract_full(message):
    '''
    Extracts the html-free message body from an email as
    a dictionary object
    '''
    
    raw = str(read_main_mail(message))
    #Trying filtering out all html emails
    #no_html = strip_tags(raw)
    
    return {'email': raw, 'sender': message['From'], 'date': message['Date'], 'title': message['Subject'], 'to': message['To']}#no_html

def extract_body(message):
    '''
    Extracts the html-free message body from an email
    '''

    raw = str(read_main_mail(message))
    #Currently filtering out all html emails, but
    # I'm paranoid
    no_html = strip_tags(raw)
    
    return no_html


def parse_into_emails(mbox):
    '''
    Converts an mbox type into a list of strings, where each
    string is the primary message body (hopefully free of html)
    '''
    return [ extract_body(message) for message in mbox ]

#=====================================================================
#Script functionality

def main(input_filename, output_prefix, min_word_count=-1, dynamic_stop_thr=-1,
    term_min_doc_thr=-1, doc_min_len_thr=-1):
   
    print "Creating original mailbox..." 
    mbox = open_mbox(input_filename)

    print "Filtering emails..."
    mbox = filter_emails(mbox)

    print "Extracting Email tags..."
    tags = extract_all_email_tags(mbox)

    print "Parsing filtered mbox into email texts"
    emails = parse_into_emails(mbox)

    print "Creating vocabulary"
    email_parser.parse_and_save_all(emails, tags, output_prefix,
        min_word_count, dynamic_stop_thr,
        term_min_doc_thr, doc_min_len_thr)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description=__doc__)

  parser.add_argument('output_prefix',
    default='email_parse')
  parser.add_argument('-input_filename',
    default='All mail Including Spam and Trash.mbox')
  parser.add_argument('-min_word_count',
    type=int, default=-1)
  parser.add_argument('-dynamic_stop_thr',
    type=int, default=30)
  parser.add_argument('-term_min_doc_thr',
    type=int, default=10)
  parser.add_argument('-doc_min_len_thr',
    type=int, default=10)

  args = parser.parse_args()

  main(
    args.input_filename,
    args.output_prefix,
    args.min_word_count,
    args.dynamic_stop_thr,
    args.term_min_doc_thr,
    args.doc_min_len_thr)

