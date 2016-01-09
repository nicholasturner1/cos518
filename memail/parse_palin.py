#!/usr/bin/env python
__doc__ = '''
Email Parsing Script for COS518

Primarily used for Sarah Palin Inbox thus far

ORDER OF OPERATIONS
-Read files
-Extract fields of interest (tag fields)
-Removing metadata lines
-Passing to email_parser.py
'''

import email_parser as ep
#Dependencies
import numpy as np
import scipy as sp
import re
import glob
import argparse

email_tags = ['From','To','Sent','Subject']

#=============================================
#IO

def grab_all_txt_files():
  '''
  Returns a list of all files ending in .txt
  within the current directory
  '''
  return glob.glob("*.txt")

def read_all_emails(email_filenames):
  '''
  Reads a list of filenames, and returns a list of 
  line-lists
  '''

  emails = []

  for filename in email_filenames:

    #Reading the file as a list of lines
    with open(filename) as f:
      lines = f.readlines()
      lines = [line.split('\n')[0] for line in lines]
      lines = [line.decode('utf-8',errors='ignore')
              for line in lines]
      f.close()

    #Appending each list to a list-list
    emails.append(lines)

  return emails 

def print_email_rep(bow_filename, vocab_filename, num_emails, email_num):
    '''
    Takes an email index (row) number from a bag of words matrix, and prints
    the verbal representation of that document. This can be useful for understanding
    which words make it through the filters below
    '''
    bow = load_bow_as_dense(bow_filename, num_emails)
    vocab = load_vocab_as_list(vocab_filename)

    rep = ""
    for i in range(len(bow[email_num,:])):
        rep += bow[email_num,i] * (" %s " % vocab[i] )

    print rep

#=============================================
#Preprocessing 

def get_email_tags(email_lines, email_filename, tag_fields=email_tags):
    '''
    Extracts the lines of the email which match a certain
    tag, and will only return the first matching line
    '''

    split_lines = [line.split(':') for line in email_lines]

    fields = {key: "" for key in tag_fields}

    fields['filename'] = email_filename

    for tag in email_tags:

        for line in split_lines:
            if tag in line[0]:

               if tag == "Sent":
                   orig_line = ":".join(line)
                   sent_index = orig_line.find('t')
                   #very hacky, but whatever not doing palin emails forever
                   trim_index = sent_index + 3
                   fields[tag] = orig_line[trim_index:]
                   break
               else:
                   fields[tag] = ":".join(line[1:])
                   break

    return fields

def get_all_email_tags(emails, email_filenames, tag_fields=email_tags):
  '''Loops get_email_tags over a list of email line-lists and filenames'''
  return [get_email_tags(emails[i], email_filenames[i], tag_fields) 
    for i in range(len(emails))]

def remove_junk_lines(emails):
  '''Misc processing to remove lines we don't want'''
  res_emails = []
  for email in emails:

    #msnbc.com lines
    email = [line for line in email 
            if 'msnbc' not in line]

    metadata_fieldnames = ['Date:','To:','From:',
        'Subject:','Sent:','Cc:','Attachments:','Recipients:',
        'Importance:','Sender:','Bcc:']

    for fieldname in metadata_fieldnames:
        email = [line for line in email
            if fieldname not in line]

    #---Original Message--- lines
    email = [line for line in email 
            if 'Original Message' not in line]

    res_emails.append(email)

  return res_emails

def perform_tfidf_transform(bow_matrix):
  '''
  Takes a numpy matrix, and transforms the values
  to account for term and document frequency

  NOT CURRENTLY USED
  '''
  from sklearn.feature_extraction.text import TfidfTransformer

  tr = TfidfTransformer(norm='l2')
  return tr.fit_transform(bow_matrix)

#=============================================
        
def main(output_prefix, email_filenames=None, min_word_count=-1,
   dynamic_stopword_thr=-1, term_min_doc_thr=-1, doc_min_len_thr=-1):

  if email_filenames is None:
    print "Defaulting to grab all txt files"
    email_filenames = grab_all_txt_files()

  print "Reading files..."
  emails = read_all_emails(email_filenames)

  print "Fetching tagged fields..."
  tags = get_all_email_tags(emails, email_filenames)
  print "Removing junk lines..."
  cleaned_emails = remove_junk_lines(emails)

  print "Creating vocabulary"
  email_parser.parse_and_save_all(cleaned_emails, tags, output_prefix,
        min_word_count, dynamic_stop_thr,
        term_min_doc_thr, doc_min_len_thr)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description=__doc__)

  parser.add_argument('output_prefix',default='email_parse')
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
    args.output_prefix,
    None,
    args.min_word_count,
    args.dynamic_stop_thr,
    args.term_min_doc_thr,
    args.doc_min_len_thr)
