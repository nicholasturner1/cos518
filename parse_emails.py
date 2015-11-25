#!/usr/bin/env python

import nltk, re, pprint
from nltk import word_tokenize
from nltk.corpus import stopwords
import numpy
# from scipy import sparse, io
import re
import glob
from sys import argv

tags = ['From','To','Subject']

junk_chars = ['{','}','#','%','&','\(','\)','\[','\]','<','>',',', '!', '.', ';', 
'?', '*', '\\', '\/', '~', '_','|','=','+','^',':','\"','\'','@','-']

#=============================================
#IO

def grab_all_txt_files():
  return glob.glob("*.txt")

def read_all_emails(email_filenames):

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
  '''saves the tagged fields as a csv file'''

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
  '''Saves a word count (vocab) dictionary as a csv with each line
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

def load_bow_as_dense(filename, num_emails):
  mat = np.fromfile(filename, dtype=np.uint8, count=-1)
  mat.reshape((num_emails, -1))
  return mat

def save_bow_as_sparse(bow):
  pass

def tag_filename(output_prefix):
  return output_prefix + "_tags.csv"

def vocab_filename(output_prefix):
  return output_prefix + "_vocab.csv"

def mat_filename(output_prefix):
  return output_prefix + ".npy"
  
#=============================================
#Preprocessing 

def get_email_tags(email_lines, email_filename, tags_fields=tags):

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
  return [get_email_tags(emails[i], email_filenames[i], tags) 
    for i in range(len(emails))]

def remove_junk_lines(emails):
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

#=============================================
#Workhorses


def create_vocabulary(emails):

    porter = nltk.PorterStemmer() # also lancaster stemmer
    wnl = nltk.WordNetLemmatizer()
    stopWords = stopwords.words("english")

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
    res_words = {}

    for k in words.keys():

        if(words[k] > num):
            res_words[k] = words[k]

    return res_words

def find_wordcounts(docs, vocab):

    bagofwords = numpy.zeros(shape=(len(docs),len(vocab)), dtype=numpy.uint8)
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
        
def main(output_prefix, email_filenames = None, min_word_count=0):

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
  if len(argv) > 1:
    main(argv[1], argv[2:])
  else:
    main('email_parse')