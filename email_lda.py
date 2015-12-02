#!/usr/bin/env python

import parse_emails as pe
import lda
from sys import argv

default_data_filename = 'data/13999.npy'
default_num_emails = 13999
default_output_prefix = "13999"

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

    model.doc_topic_.tofile('data/13999_email_x_topic.npy')
    model.topic_word_.tofile('data/13999_topic_x_word.npy')



if __name__ == '__main__':
    #really basic arg parsing bc I'm feeling lazy
    if len(argv) == 1:
        model = train_model( default_data_filename, default_num_emails )
        save_model( default_output_prefix )

    elif len(argv) == 4:
        model = train_model( argv[1], int(argv[2]) )
        save_model( model, argv[3] )
