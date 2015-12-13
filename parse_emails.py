#!/usr/bin/env python
__doc__ = '''
Email Parsing Script for COS518

Primarily used for Sarah Palin Inbox thus far

ORDER OF OPERATIONS
-Read files
-Extract fields of interest (tag fields)
-Removing metadata lines
-Removing junk characters (defined below)
-Converting to lowercase
-Removing common stop words
-Removing terms containing numbers
-Removing short terms (length < 3)
-Lemmatizing across common forms of a word
-Filtering out terms which are very rare (optional - not default)
-Filtering out extremely common terms (optional - default)
-Filtering out terms which appear in very few documents (optional - default)
-Filtering out documents with very few terms (optional - default)

Saves a copy of the tag fields for the full dataset,
 as well as one for the emails surviving the filters above
 (the former of these is indicated by 'full')

Does the same for the bag-of-words matrix
'''

import re
import glob
import argparse

#Dependencies
import numpy as np
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
import scipy as sp

#=============================================
stemmer = nltk.PorterStemmer() # also lancaster stemmer
lemmatizer = nltk.WordNetLemmatizer()
stopWords = stopwords.words("english")

#Fields wh
tags = ['From','To','Subject']

#Filtered out of all email texts within create_vocabulary
junk_chars = ['{','}','#','%','&','\(','\)','\[','\]','<','>',',', '!', '.', ';', 
'?', '*', '\\', '\/', '~', '_','|','=','+','^',':','\"','\'','@','-']

#NOT currently filtered
#junk_words = ['re','subject','sent','cc','bcc','com','http']

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

def save_email_tags(all_email_tags, filename):
  '''
  Saves the tag fields (see get_email_tags below)
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
      tag_dicts.append( { header_line[i]: line[i] for i in range(len(header_line))} )

    return tag_dicts
    
    

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
#Functions to abstract filename modifications
def tag_filename(output_prefix):
  return output_prefix + "_tags.csv"

def vocab_filename(output_prefix):
  return output_prefix + "_vocab.csv"

def mat_filename(output_prefix):
  return output_prefix + ".npy"

#=============================================
#Preprocessing 

def get_email_tags(email_lines, email_filename, tags_fields=tags):
    '''
    Extracts the lines of the email which match a certain
    tag, and will only return the first matching line
    '''

    split_lines = [line.split(':') for line in email_lines]

    fields = {key: "" for key in tags}

    fields['filename'] = email_filename

    for tag in tags:

        for line in split_lines:
            if tag in line[0]:
               fields[tag] = "".join(line[1:])
               break

    return fields

def get_all_email_tags(emails, email_filenames, tag_fields=tags):
  '''Loops get_email_tags over a list of email line-lists and filenames'''
  return [get_email_tags(emails[i], email_filenames[i], tags) 
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

def contains_num(word):
    num_strings = ['0','1','2','3','4','5','6','7','8','9']

    for num in num_strings:
        if num in word:
            return True
    return False

#=============================================
#Workhorses

def create_corpus_vocabulary(emails):
    '''
    Preprocesses the words in all emails, forms
    a dictionary mapping a vocabulary of words
    to the number of occurrences of that word within
    the corpus
    '''
    print "Importing nltk dependencies (can take a bit)"
    print "Processing documents"

    vocab = {}
    res_emails = []

    for i in range(len(emails)):
      print "Email: # %d" % (i+1)

      tokens = process_email_tokens( emails[i] )

      vocab = add_tokens_to_vocab( vocab, tokens )

      res_emails.append(tokens)

    return(vocab, res_emails)

def process_email_tokens( email ):
    '''
    Takes an individual email, splits it into tokens,
    and filters that list of tokens for various issues
    '''
    #Collapsing across lines
    email_text = ' '.join( email )

    # remove noisy characters
    junk_removed = re.sub('[%s]' % ''.join(junk_chars), ' ', email_text)

    #Splitting document into words
    tokens = word_tokenize(junk_removed)

    #Converts to lowercase
    tokens = [w.lower() for w in tokens]

    #Removes stopwords from argument
    tokens = [w for w in tokens if w not in stopWords]

    #Removes 'junk words' defined above - NOT CURRENTLY USED
    #tokens = [w for w in tokens if w not in junk_words]

    #Removes words containing a number (filtering dates, prices, etc.)
    tokens = [w for w in tokens if not contains_num(w)]

    #Removes short terms
    tokens = [w for w in tokens if len(w) >= 3]

    #Lemmatizes words to condense across grammatical forms
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    #Stemming is similar to lemmatization, but works differently
    #tokens = [stemmer.stem(t) for t in tokens]

    return tokens

def add_tokens_to_vocab( vocab, tokens ):
    '''
    Takes a dictionary which tracks the total corpus
    bag of word count so far, and adds new tokens to the record
    '''
    
    for t in tokens: 
    # this is a hack but much faster than lookup each
    # word within many dict keys
      try:
        vocab[t] = vocab[t]+1
      except:
        vocab[t] = 1

    return vocab

def wordcount_filter(words, num=5):
    '''
    Filters the dictionary above for words which
    occur more than ${num} times
    '''
    res_words = {}

    for k in words.keys():

        if(words[k] > num):
            res_words[k] = words[k]

    return res_words

def find_wordcounts(docs, vocab):
    '''
    Forms the document-term matrix over preprocessed
    line-lists and vocabulary
    '''

    bagofwords = np.zeros(shape=(len(docs),len(vocab)), dtype=np.uint8)
    vocabIndex={}
    vocab = sorted(vocab.keys())

    for i in range(len(vocab)):
       vocabIndex[vocab[i]]=i

    for i in range(len(docs)):
        doc = docs[i]

        for t in doc:
           index_t=vocabIndex.get(t)
           if index_t>=0:
              bagofwords[i,index_t]=bagofwords[i,index_t]+1

    return bagofwords, vocab

def remove_indices_from_bow(bow, aux, to_remove, axis):
    '''Removes corresponding indices from a bow matrix
    and an auxiliary list (either the vocab or the email id's
    w/ tag fields'''
    bow = np.delete(bow, to_remove, axis)
    to_remove = to_remove[::-1]
    aux = list(aux) # copying so references are intact

    print "%d items to remove" % to_remove.size
    for i in to_remove:
        del aux[i]

    return bow, aux

def dynamic_stopword_filter(bow, vocab=None, threshold=None):
    '''Filtering out the ${threshold} most common words'''

    word_counts = bow.sum(0)

    word_ranks = np.argsort(word_counts)

    to_remove = np.where(word_ranks >= (word_ranks.size - threshold) )[0]

    return remove_indices_from_bow(bow, vocab, to_remove, 1)

def term_min_doc_filter(bow, vocab, threshold):
    '''
    Filters out terms which appear in fewer than ${threshold} 
    documents
    '''

    #binarize
    bow_copy = np.copy(bow)
    bow_copy[np.nonzero(bow_copy)] = 1

    word_counts = bow_copy.sum(0)

    to_remove = np.where( word_counts < threshold )[0]

    return remove_indices_from_bow(bow, vocab, to_remove, 1)

def document_min_length_filter(bow, tags, threshold):
    '''Removing documents with fewer than threshold terms'''

    doc_counts = bow.sum(1)

    to_remove = np.where(doc_counts < threshold)[0]

    return remove_indices_from_bow(bow, tags, to_remove, 0)
    

#=============================================
        
def main(output_prefix, email_filenames=None, min_word_count=-1,
   dynamic_stopword_thr=-1, term_min_doc_thr=-1, doc_min_len_thr=-1):

  if email_filenames is None:
    print "Defaulting to grab all txt files"
    email_filenames = grab_all_txt_files()

  print "Reading files..."
  emails = read_all_emails(email_filenames)

  print "Fetching tagged fields..."
  email_tags = get_all_email_tags(emails, email_filenames)
  print "Removing junk lines..."
  cleaned_emails = remove_junk_lines(emails)

  print "Generating word counts..."
  vocabulary, cleaned_emails = create_corpus_vocabulary(cleaned_emails)

  if min_word_count > 0:
    print "Filtering word counts to those > %d..." % (min_word_count)
    vocabulary = wordcount_filter(vocabulary, min_word_count)

  print "Generating data matrix..."
  bow, vocab_list = find_wordcounts(cleaned_emails, vocabulary)

  if dynamic_stopword_thr > 0:
    print "Filtering out common terms..."
    bow, vocab = dynamic_stopword_filter(bow, vocab_list,
                      dynamic_stopword_thr)

  if term_min_doc_thr > 0:
    print "Filtering out uncommon terms..."  
    bow, vocab = term_min_doc_filter(bow, vocab_list, 
                      term_min_doc_thr)

  if doc_min_len_thr > 0:
    print "Filtering out small documents..."
    filtered_bow, filtered_email_tags = document_min_length_filter(
                      bow, email_tags, doc_min_len_thr)

  print "FINAL Bag-of-Words Matrix Dimensions:" 
  print filtered_bow.shape
  print 

  print "Saving tagged fields..."
  save_email_tags(filtered_email_tags, tag_filename(output_prefix))
  save_email_tags(email_tags, tag_filename(output_prefix + "_full"))

  print "Saving vocabulary..."
  save_vocabulary(vocab, vocab_filename(output_prefix))

  print "Saving data matrix..."
  save_bow_as_dense(filtered_bow, mat_filename(output_prefix))
  save_bow_as_dense(bow, mat_filename(output_prefix + "_full"))

  print "Done!"

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
