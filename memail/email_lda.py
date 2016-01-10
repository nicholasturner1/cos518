#!/usr/bin/env python

import email_io as eio
import email_parser as ep
import model_interface as mi

#Dependencies
import gensim
import numpy as np
import argparse


#=====================================================================
#Training Functions


def train_model(data_filename, num_topics=10, num_passes=1,
    topic_x_word=True, email_x_topic=True, binarize=False):

    print "Loading data..."
    data = eio.load_bow(data_filename)

    if binarize:
        data[np.nonzero(data)] = 1

    #Converting to gensim corpus
    corpus = gensim.matutils.Dense2Corpus(data, documents_columns=False)

    print "Beginning training..."
    model = gensim.models.ldamodel.LdaModel(corpus, 
              num_topics=num_topics, passes=num_passes,
              alpha=0.01,eta=0.01)

    print "Done"
    if email_x_topic:
        ext = run_inference(model, corpus)
    if topic_x_word:
        txw = extract_topic_word_dist(model)

    if email_x_topic and topic_x_word:
        return model, ext, txw
    elif email_x_topic:
        return model, ext
    elif topic_x_word:
        return model, txw
    else:
        return model


def run_inference_over_file(data_filename, model_filename, save=False,
     num_topics=None, output_prefix=None):

    print "Loading data..."
    data = eio.load_bow(data_filename)

    #Converting to gensim corpus
    corpus = gensim.matutils.Dense2Corpus(data, documents_columns=False)

    print "Loading model..."
    model = mi.load_model( model_filename )

    ext = run_inference(model, corpus)

    if save:
        assert num_topics is not None
        assert output_prefix is not None

        num_emails = ext.shape[0]
        filenames = output_filenames( output_prefix, num_emails, num_topics )

        ext.tofile( filenames['email_x_topic'] )

    return ext


def run_inference(model_obj, corpus):

    print "Performing inference over data..."
    email_x_topic = model_obj.inference(corpus)[0]
    #Normalizing weights
    email_x_topic = email_x_topic / email_x_topic.sum(1, keepdims=True)

    return email_x_topic


def extract_topic_word_dist(model_obj):

    print "Extracting topic distributions..."
    topic_x_word = model_obj.state.get_lambda()
    #Normalizing topics
    topic_x_word = topic_x_word / topic_x_word.sum(1, keepdims=True)

    return topic_x_word


#=====================================================================
#Debug/Display Functions

def print_top_n_words( topic_x_word_matrix, vocab_filename, num_words=10 ):
    '''Neatly prints the top {num_words} words of each topic'''

    vocabulary = np.array( eio.load_vocab_as_list( vocab_filename ), dtype=object)
    num_topics = topic_x_word_matrix.shape[0]

    top_word_lists = []
    for i in range(num_topics):
        topic_dist = topic_x_word_matrix[i,:]

        sort_indices = np.argsort( topic_dist )

        sorted_words = vocabulary[sort_indices]
        sorted_words = sorted_words[::-1]
        top_word_lists.append( sorted_words[:num_words] )

    return top_word_lists


def print_top_n_people( social_x_sender_matrix, sender_name_array, num_people=10):
    '''
    Assumes sender_name_aray containing n names is a [n][0][0] array
    '''
    num_clusters = social_x_sender_matrix.shape[0]
    top_sender_lists = []
    
    sender_name_list=[]
    for i in range(len(sender_name_array)):
        sender_name_list.append(str(sender_name_array[i][0][0]))
  
    sender_name_list = np.array(sender_name_list, dtype=object)   

   
    print "Finding the top %d people for %d groups" %(num_people, num_clusters) 
    
    for i in range(num_clusters):
        cluster_dist = social_x_sender_matrix[i,:]
        sort_indices = np.argsort( cluster_dist )
        sorted_people = sender_name_list[sort_indices]
    	sorted_people = sorted_people[::-1]
        top_sender_lists.append( sorted_people[:num_people] )
        #print "appending for cluster %d: %s" %(i, sorted_people[:num_people])
            
    return top_sender_lists

def output_filenames( output_prefix, num_emails, num_topics ):
    return {
        'email_x_topic': output_prefix + "_LDA_email_x_topic_%d.npy" % num_emails,
        'topic_x_word' : output_prefix + "_LDA_topic_x_word_%d.npy"  % num_topics,
        'model'        : output_prefix + "_LDA_model"
        }

#=====================================================================
#Script functionality

def main( data_filename, num_topics, num_passes, output_prefix ):

    model, ext, txw = train_model( data_filename, num_topics, 
                                   num_passes, True, True )

    #Adding the number of rows to each saved result file
    # to assist in reading
    num_emails = ext.shape[0]
    num_topics = txw.shape[0]

    filenames = output_filenames( output_prefix, num_emails, num_topics )

    ext.tofile( filenames['email_x_topic'] )
    txw.tofile( filenames['topic_x_word']  )
    model.save( filenames['model'] )

if __name__ == '__main__':
   
    parser = argparse.ArgumentParser(description = __doc__)

    parser.add_argument('data_filename',
        default='data/14453.npy',
        help="Name of data file")
    parser.add_argument('-num_topics',
        type=int, default=15,
        help="Number of topics to fit")
    parser.add_argument('-num_passes',
        type=int, default=1,
        help="Number of times to pass over dataset")
    parser.add_argument('output_prefix',
        default='14453',
        help="Prefix for saved output")

    args = parser.parse_args()

    main(args.data_filename,
         args.num_topics,
         args.num_passes,
         args.output_prefix)

