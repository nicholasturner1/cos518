#!/usr/bin/env python
__doc__ = '''
Module for IO of email parsing data
'''

#Dependencies
import numpy as np
import scipy.sparse as sp
import dateutil.parser
import mailbox
import base64


###################################################################
#Functions to abstract filename modifications
def tag_filename(output_prefix):
  return output_prefix + "_tags.csv"

def vocab_filename(output_prefix):
  return output_prefix + "_vocab.csv"

def mat_filename(output_prefix):
  return output_prefix + ".npy"

###################################################################
#data matrices - bag_of_words, email_x_topic, topic_x_word

def save_bow(bow, filename):
    save_bow_as_sparse(bow, filename)

def save_bow_as_sparse(bow, filename):
  '''
  Using a sparse matrix for storage should decrease disk usage,
  and make loading much easier (removing the need to explicitly
  write the number of rows
  '''
  to_save = np.array( sp.find(sp.coo_matrix(bow)), dtype=np.uint32 ) 

  to_save.tofile(filename)

def load_bow(filename):
  d = load_datamat(filename, 3, np.uint32)

  i, j, d = d[0,:], d[1,:], d[2,:]

  #the shape business should be safe, since the parser
  # guarantees that every doc/term is used
  sp_mat = sp.coo_matrix((d,(i,j)),
        shape=( np.max(i)+1, np.max(j)+1 )
        )

  return sp_mat.todense()

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

###################################################################
#vocab

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


def read_clean_lines(filename):
    '''
    Reads the lines of a file, strips off the enter (\n)
    character, returns the result
    '''
    
    with open(filename) as f:
      lines = f.readlines()
      lines = [line.split('\n')[0] for line in lines]
      f.close()

    return lines

def load_vocab_as_list(filename):
  '''Loads a vocab file as a list of words'''

  vocab = []

  lines = read_clean_lines(filename)
 
  for line in lines:
    vocab.append( line.split(',')[1] )

  return vocab

def load_vocab_index(filename):
    '''
    Loads a vocab file as a dict mapping words to their
    bow indices
    '''

    vocab_index = {}

    lines = read_clean_lines(filename)

    for line in lines:
      index, word = line.split(',')
      vocab_index[ word ] = int(index)

    return vocab_index

###################################################################
#tags 

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

def load_tags(filename):
    '''
    Loads a tags file as a list of field dicts

    Assumes that the file has a header line
    '''
    
    tag_dicts = []

    lines = read_clean_lines(filename)
    lines = [line.split(';;') for line in lines]

    header_line = lines[0]

    #Creating dicts, appending to lists
    for line in lines[1:]:
      print line
      tag_dicts.append( { header_line[i]: line[i] for i in range(len(header_line))} )

    return tag_dicts

###################################################################
#mbox files

def read_main_mail(message):
    '''Extracts the message body from an email message'''

    message_layer = message
    while message_layer.is_multipart():
        message_layer = message_layer.get_payload()[0]
   
    result = message_layer.get_payload()

    if message_layer['Content-Transfer-Encoding'] == 'base64':
        result = base64.b64decode(result)

    return result

def import_message( message ):
    '''
    Translates an mbox message to a dict structure handled by
    the GUI
    '''
    message_dict = {}

    message_dict['email'] = read_main_mail(message)
    message_dict['sender'] = safe_extract(message, "From")
    message_dict['to'] = safe_extract(message, "To")
    message_dict['title'] = safe_extract(message, "Subject")
    message_dict['date'] = safe_extract(message, "Date")

    return message_dict

def import_mbox(mbox_filename):
    
    mbox = mailbox.mbox( mbox_filename )

    dict_list = []

    for message in mbox:

        dict_list.append( import_message(message) )

    return dict_list

def safe_extract(message, key):
    return message[key] if message.has_key(key) else ""

