#!/usr/bin/env python
__doc__ = '''
Email Parsing Script for COS518

ORDER OF OPERATIONS
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
import email_io

#Dependencies
import numpy as np
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords

#=============================================
stemmer = nltk.PorterStemmer() # also lancaster stemmer
lemmatizer = nltk.WordNetLemmatizer()
stopWords = stopwords.words("english")

#Fields wh
tags = ['From','To','Sent','Subject']

#Filtered out of all email texts within process_tokens
junk_chars = ['{','}','#','%','&','\(','\)','\[','\]','<','>',',', '!', '.', ';', 
'?', '*', '\\', '\/', '~', '_','|','=','+','^',':','\"','\'','@','-']

#filtering URL tokens
junk_words = ['com','http','edu','www','gov','biz']

#=============================================
#Helper functions
def contains_num(word):
    num_strings = ['0','1','2','3','4','5','6','7','8','9']

    for num in num_strings:
        if num in word:
            return True
    return False


#=============================================
#Main functionality
def tokenize_and_count(emails):
    '''
    Preprocesses the words in all emails, forms
    a dictionary mapping a vocabulary of words
    to the number of occurrences of that word within
    the corpus
    '''
    print "Processing documents"

    word_counts = {}
    res_emails = []

    for i in range(len(emails)):
      print "Email: # %d of %d" % (i+1, len(emails))

      tokens = process_email_tokens( emails[i] )

      word_counts = add_tokens_to_counts( word_counts, tokens )

      res_emails.append(tokens)

    return(word_counts, res_emails)

def process_email_tokens( email ):
    '''
    Takes an individual email, splits it into tokens,
    and filters that list of tokens for various issues
    '''

    # remove noisy characters
    email = email.decode('ascii',errors='ignore')
    email = email.replace('\n','').replace('\r','')
    junk_removed = re.sub('[%s]' % ''.join(junk_chars), ' ', email)

    #Splitting document into words
    tokens = word_tokenize(junk_removed)

    #Converts to lowercase
    tokens = [w.lower() for w in tokens]

    #Removes stopwords from argument
    tokens = [w for w in tokens if w not in stopWords]

    #Removes 'junk words' defined above
    tokens = [w for w in tokens if w not in junk_words]

    #Removes words containing a number (filtering dates, prices, etc.)
    tokens = [w for w in tokens if not contains_num(w)]

    #Removes urls and html tags (not ready yet)
    #tokens = [w for w in tokens if not contains_url(w)]

    #Removes short terms
    tokens = [w for w in tokens if len(w) >= 3]

    #Lemmatizes words to condense across grammatical forms
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    #Stemming is similar to lemmatization, but works differently
    #tokens = [stemmer.stem(t) for t in tokens]

    return tokens

def add_tokens_to_counts( word_counts, tokens ):
    '''
    Takes a dictionary which tracks the total corpus
    bag of word count so far, and adds new tokens to the record
    '''
    
    for t in tokens: 
    # this is a hack but much faster than lookup each
    # word within many dict keys
      try:
        word_counts[t] = word_counts[t]+1
      except:
        word_counts[t] = 1

    return word_counts

def wordcount_filter(word_counts, thr=5):
    '''
    Filters the dictionary above for words which
    occur more than ${num} times
    '''
    res = {}

    for word, count in word_counts.iteritems():

        if(count > thr):
            res[word] = count

    return res

def vocab_index_from_list(vocab_list):
    '''Creates a dict mapping words to indices'''
    return { vocab_list[i] : i for i in range(len(vocab_list)) }

def map_text_to_bow(email_text, vocab_list=None, vocab_index=None):
    '''
    Maps a single email's text to a bow vector as specified by
    the vocabulary
    '''
    return map_text_list_to_bow([email_text], vocab_list, vocab_index)

def map_text_list_to_bow(email_list, vocab_list=None, vocab_index=None):

    email_tokens = [process_email_tokens(email) for email in email_list]

    return map_tokens_to_bow(email_tokens, vocab_list, vocab_index)

def map_tokens_to_bow(docs, vocab_list=None, vocab_index=None):
    '''
    Forms the document-term matrix over preprocessed
    line-lists and vocabulary
    '''

    assert( (vocab_list is not None) or (vocab_index is not None) )

    if vocab_index is None:
      vocab_index = vocab_index_from_list( sorted(vocab_list) )

    bagofwords = np.zeros(shape=(len(docs),len(vocab_index)), dtype=np.uint8)

    for i in range(len(docs)):
        doc = docs[i]

        for word in doc:
           index = vocab_index.get(word)
           if (index >= 0) and (bagofwords[i,index] < 255):
              bagofwords[i,index] = bagofwords[i,index]+1

    return bagofwords

def remove_indices_from_bow(bow, aux, to_remove, axis):
    '''
    Removes corresponding indices from a bow matrix
    and an auxiliary list (either the vocab or the email id's
    w/ tag fields
    '''
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

    #i, j, d = sp.find(bow)
    #binarize
    #d = np.ones(d.shape)
    #bow_copy = coo_matrix((d,(i,j)),shape=bow.shape)
    print "copying..."
    bow_copy = np.copy(bow)
    bow_copy[np.nonzero(bow)] = 1
    print "done"

    word_counts = bow.sum(0)

    to_remove = np.where( word_counts < threshold )[0]

    return remove_indices_from_bow(bow, vocab, to_remove, 1)

def document_min_length_filter(bow, tags, threshold):
    '''Removing documents with fewer than threshold terms'''

    #scipy version of ravel can be buggy
    doc_counts = bow.sum(1)

    to_remove = np.where(doc_counts < threshold)[0]

    return remove_indices_from_bow(bow, tags, to_remove, 0)
    

#=============================================
#Main interface functions

def parse(email_list, email_tags,
   min_word_count=-1, dynamic_stopword_thr=-1, term_min_doc_thr=-1, doc_min_len_thr=-1):

  print "Generating word counts..."
  word_counts, cleaned_emails = tokenize_and_count(email_list)

  if min_word_count > 0:
    print "Filtering word counts to those > %d..." % (min_word_count)
    word_counts = wordcount_filter(word_counts, min_word_count)

  #Only needed the counts for the filter above
  vocab = sorted( word_counts.keys() )

  print "Generating data matrix..."
  bow = map_tokens_to_bow(cleaned_emails, vocab)

  if dynamic_stopword_thr > 0:
    print "Filtering out common terms..."
    bow, vocab = dynamic_stopword_filter(bow, vocab,
                      dynamic_stopword_thr)

  if term_min_doc_thr > 0:
    print "Filtering out uncommon terms..."  
    bow, vocab = term_min_doc_filter(bow, vocab, 
                      term_min_doc_thr)

  if doc_min_len_thr > 0:
    print "Filtering out small documents..."
    filtered_bow, filtered_email_tags = document_min_length_filter(
                      bow, email_tags, doc_min_len_thr)

  print "FINAL Bag-of-Words Matrix Dimensions:" 
  print filtered_bow.shape

  return bow, filtered_bow, email_tags, filtered_email_tags, vocab

def save_all(bow_matrix, email_tags, vocabulary, output_prefix,
   filtered_email_tags=None, filtered_bow=None):

  print "Saving tagged fields..."
  email_io.save_email_tags(filtered_email_tags, 
                           email_io.tag_filename(output_prefix))
  email_io.save_email_tags(email_tags, 
                           email_io.tag_filename(output_prefix + "_full"))

  print "Saving vocabulary..."
  email_io.save_vocabulary(vocabulary, 
                           email_io.vocab_filename(output_prefix))

  print "Saving data matrix..."
  email_io.save_bow_as_dense(filtered_bow, 
                             email_io.mat_filename(output_prefix))
  email_io.save_bow_as_dense(bow_matrix, 
                             email_io.mat_filename(output_prefix + "_full"))

def parse_and_save_all(email_text_lines, email_tags, output_prefix,
  min_word_count=-1, dynamic_stopword_thr=-1, term_min_doc_thr=-1, doc_min_len_thr=-1):

  bow, f_bow, et, f_et, vocab = parse(email_text_lines, email_tags, 
                                   min_word_count, dynamic_stopword_thr, 
                                   term_min_doc_thr, doc_min_len_thr)

  save_all(bow, et, vocab, output_prefix, f_et, f_bow)

  print "Done!"
