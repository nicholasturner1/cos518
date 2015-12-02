#!/usr/bin/env python

import parse_emails as pe
import lda
import numpy as np
from sys import argv

default_data_filename = "data/13999.npy"
default_num_emails = 13999
default_output_prefix = "data/13999"

def train_model(data_filename = 'data/13999.npy', num_emails = 13999):

    #Constants
    n_topics = 10
    n_iter = 2000
    random_state = 1

    #Loading bag-of-words dataset
    data = pe.load_bow_as_dense(data_filename, num_emails)

    #lda package only accepts count matrices, not tfidf
    model = lda.LDA(n_topics=n_topics, 
        n_iter=n_iter, 
        random_state=random_state)

    #Training LDA model
    model.fit(m)

def save_model(model_obj, output_prefix):

    model_obj.doc_topic_.tofile( output_prefix + "_email_x_topic.npy" )
    model_obj.topic_word_.tofile( output_prefix + "_topic_x_word.npy" )

def print_top_n_words( topic_x_word_matrix, vocab_filename, num_words=10 ):

    vocabulary = np.array( pe.load_vocab_as_list( vocab_filename ), dtype=object)

    num_topics = topic_x_word_matrix.shape[0]

    top_word_lists = []
    for i in range(num_topics):
        topic_dist = topic_x_word_matrix[i,:]

        sort_indices = np.argsort( topic_dist )

        sorted_words = vocabulary[sort_indices]
        top_word_lists.append( sorted_words[:num_words] )

    return top_word_lists

if __name__ == '__main__':
    #really basic arg parsing bc I'm feeling lazy
    if len(argv) == 1:
        model = train_model( default_data_filename, default_num_emails )
        save_model( default_output_prefix )

    elif len(argv) == 4:
        model = train_model( argv[1], int(argv[2]) )
        save_model( model, argv[3] )
