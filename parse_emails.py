#!/usr/bin/env python
import re
import glob
from sys import argv

#Dependencies
import numpy as np
#nltk (within create_vocabulary)
#sklearn.feature_extraction.text

tags = ['From','To','Subject']

junk_chars = ['{','}','#','%','&','\(','\)','\[','\]','<','>',',', '!', '.', ';', 
'?', '*', '\\', '\/', '~', '_','|','=','+','^',':','\"','\'','@','-']

#=============================================
#IO

def grab_all_txt_files():
  return glob.glob("*.txt")

def read_all_emails(email_filenames):
  '''
  Reads a list of filenames, and returns a list of 
  line-lists
  '''

  emails = []

  for filename in email_filenames:
    with open(filename) as f:
      lines = f.readlines()
      lines = [line.split('\n')[0] for line in lines]
      lines = [line.decode('ascii',errors='ignore')
              for line in lines]
      f.close()
    emails.append(lines)

  return emails

def save_email_tags(all_email_tags, filename):
  '''
  Saves the tag fields (see get_email_tags below)
  as a csv with a header line
  '''

  keys = sorted(all_email_tags[0].keys())

  with open(filename,'w+') as f:

    f.write( ','.join(keys) )
    f.write('\n')

    for email_tags in all_email_tags:
      fields = [email_tags[key] for key in keys]
      f.write( ','.join(fields) )
      f.write('\n')

    f.close()

def save_vocabulary(vocab_dict, filename):
  '''
  Saves a word count (vocab) dictionary as a csv with each line
  taking the format

  word_index,word
  '''

  words = sorted(vocab_dict)

  with open(filename,'w+') as f:

    for i in range(len(words)):
      f.write( '%d,%s' % (i,words[i]) )
      f.write('\n')

    f.close()

def save_bow_as_dense(bow, filename):
  bow.tofile(filename)

def save_bow_as_sparse(bow):
  '''Could be useful later'''
  pass

def load_bow_as_dense(filename, num_emails):
  mat = np.fromfile(filename, dtype=np.uint8, count=-1)
  return mat.reshape((num_emails, -1))

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

    #---Original Message--- lines
    email = [line for line in email 
            if 'Original Message' not in line]

    res_emails.append(email)

  return res_emails

def perform_tfidf_transform(bow_matrix):
  '''
  Takes a numpy matrix, and transforms the values
  to account for term and document frequency
  '''
  from sklearn.feature_extraction.text import TfidfTransformer

  tr = TfidfTransformer(norm='l2')
  return tr.fit_transform(bow_matrix)

#=============================================
#Workhorses

def create_vocabulary(emails):
    '''
    Preprocesses the words in all emails, forms
    a dictionary mapping a vocabulary of words
    to the number of occurrences of that word within
    the corpus
    '''
    print "Importing nltk dependencies (can take a bit)"
    import nltk
    from nltk import word_tokenize
    from nltk.corpus import stopwords

    porter = nltk.PorterStemmer() # also lancaster stemmer
    wnl = nltk.WordNetLemmatizer()
    stopWords = stopwords.words("english")
    print "Processing documents"

    vocab = {}
    res_emails = []

    for email in emails:

      #Collapsing across lines
      email_text = ' '.join(email)

      # remove noisy characters; tokenize
      junk_removed = re.sub('[%s]' % ''.join(junk_chars), ' ', email_text)
      tokens = word_tokenize(junk_removed)

      # lotsa processing
      tokens = [w.lower() for w in tokens]
      tokens = [w for w in tokens if w not in stopWords]
      tokens = [wnl.lemmatize(t) for t in tokens]
      tokens = [porter.stem(t) for t in tokens]

      for t in tokens: 
      # this is a hack but much faster than lookup each
      # word within many dict keys
        try:
          vocab[t] = vocab[t]+1
        except:
          vocab[t] = 1

      res_emails.append(tokens)

    return(vocab, res_emails)

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

    return bagofwords

#=============================================
        
def main(output_prefix, min_word_count=0, email_filenames=None):

  if email_filenames is None:
    print "Defaulting to grab all txt files"
    email_filenames = grab_all_txt_files()

  print "Reading files..."
  emails = read_all_emails(email_filenames)

  print "Fetching tagged fields..."
  email_tags = get_all_email_tags(emails, email_filenames)
  print "Saving tagged fields..."
  save_email_tags(email_tags, tag_filename(output_prefix))

  print "Removing junk lines..."
  cleaned_emails = remove_junk_lines(emails)

  print "Generating word counts..."
  vocabulary, cleaned_emails = create_vocabulary(cleaned_emails)

  if min_word_count > 0:
    print "Filtering word counts..."
    vocabulary = wordcount_filter(vocabulary)
  print "Saving vocabulary..."
  save_vocabulary(vocabulary, vocab_filename(output_prefix))

  print "Generating data matrix..."
  bow = find_wordcounts(cleaned_emails, vocabulary)
  print "Saving data matrix..."
  save_bow_as_dense(bow, mat_filename(output_prefix))

  print "Done!"

if __name__ == "__main__":
  if len(argv) == 3:
    main(argv[1], argv[2])
  elif len(argv) > 3:
    main(argv[1], argv[2], argv[3:])
  else:
    main('email_parse')
