#!/usr/bin/env python
__doc__ = '''
Module for IO of email parsing data
'''

#Dependencies
import numpy as np
import dateutil.parser
import mailbox
import base64

#=============================================
#Functions to abstract filename modifications
def tag_filename(output_prefix):
  return output_prefix + "_tags.csv"

def vocab_filename(output_prefix):
  return output_prefix + "_vocab.csv"

def mat_filename(output_prefix):
  return output_prefix + ".npy"
#=============================================

def save_email_tags(all_email_tags, filename):
  '''
  Saves the tag fields (a list of dicts)
  as a csv with a header line, delimited by ;;
  '''

  keys = sorted(all_email_tags[0].keys())

  with open(filename,'w+') as f:

    f.write( ';;'.join(keys) )
    f.write('\n')

    for email_tags in all_email_tags:
      fields = [email_tags[key] for key in keys]
      f.write( ';;'.join(fields) )
      f.write('\n')

    f.close()

def save_vocabulary(vocab_list, filename):
  '''
  Saves a word count (vocab) dictionary as a csv with each line
  taking the format

  word_index,word
  '''

  #words = sorted(vocab_dict)

  with open(filename,'w+') as f:

    for i in range(len(vocab_list)):
      f.write( '%d,%s' % (i,vocab_list[i]) )
      f.write('\n')

    f.close()

def save_bow_as_dense(bow, filename):
  bow.tofile(filename)

def save_bow_as_sparse(bow):
  '''Could be useful later'''
  pass

def load_datamat(filename, num_rows, dtype):
  mat = np.fromfile(filename, dtype=dtype, count=-1)
  return mat.reshape((num_rows, -1))

def load_float64(filename, num_rows):
  return load_datamat(filename, num_rows, np.float64)

def load_int8(filename, num_rows):
  return load_datamat(filename, num_rows, np.uint8)

def load_bow_as_dense(filename, num_emails):
  return load_int8(filename, num_emails)

def load_email_x_topic(filename, num_emails):
  return load_float64(filename, num_emails)

def load_topic_x_word(filename, num_topics):
  return load_float64(filename, num_topics)
  
def load_social_results_as_dict(filename):
  return sp.io.loadmat(filename)

def load_vocab_as_list(filename):
  '''Loads a vocab file as a list of words'''

  vocab = []

  with open(filename) as f:
    lines = f.readlines()
    lines = [line.split('\n')[0] for line in lines]
    f.close()

  for line in lines:
    vocab.append( line.split(',')[1] )

  return vocab

def load_tags(filename):
    '''
    Loads a tags file as a list of field dicts

    Assumes that the file has a header line
    '''
    
    tag_dicts = []

    with open(filename) as f:
      lines = f.readlines()
      lines = [line.split('\n')[0] for line in lines]
      lines = [line.split(';;') for line in lines]
      f.close()

    header_line = lines[0]

    #Creating dicts, appending to lists
    for line in lines[1:]:
      print line
      tag_dicts.append( { header_line[i]: line[i] for i in range(len(header_line))} )

    return tag_dicts

def read_main_mail(message):
    '''Extracts the message body from an email message'''

    message_layer = message
    while message_layer.is_multipart():
        message_layer = message_layer.get_payload()[0]
   
    result = message_layer.get_payload()

    if message_layer['Content-Transfer-Encoding'] == 'base64':
        result = base64.b64decode(result)

    return result

def import_mbox(mbox_filename):
    
    mbox = mailbox.mbox( mbox_filename )

    dict_list = []

    for message in mbox:
        message_dict = {}

        message_dict['email'] = read_main_mail(message)
        message_dict['sender'] = safe_extract(message, "From")
        message_dict['to'] = safe_extract(message, "To")
        message_dict['title'] = safe_extract(message, "Subject")
        message_dict['date'] = safe_extract(message, "Date")

        dict_list.append( message_dict )

    return dict_list

def safe_extract(message, key):
    return message[key] if message.has_key(key) else ""

