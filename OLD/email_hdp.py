#!/usr/bin/env python

import parse_emails as pe
import gensim
import numpy as np
import argparse

def train_model(data_filename, num_emails, vocab_filename,
    topic_x_word=True, email_x_topic=True):

    print "Loading data..."
    data = pe.load_bow_as_dense(data_filename, num_emails)

    vocab_list = pe.load_vocab_as_list( vocab_filename )
    vocab_dict = {i:vocab_list[i] for i in range(len(vocab_list))}

    #Converting to gensim corpus
    corpus = gensim.matutils.Dense2Corpus(data, documents_columns=False)

    print "Beginning training..."
    model = gensim.models.hdpmodel.HdpModel(corpus, id2word=vocab_dict)

    print "Done"
    if email_x_topic:
        ext = extract_email_topic_dist(model, corpus)
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

def extract_email_topic_dist(model_obj, corpus):

    print "Performing inference over data..."
    email_x_topic = model_obj.inference(corpus)
    #Normalizing weights
    email_x_topic = email_x_topic / email_x_topic.sum(1, keepdims=True)

    return email_x_topic

def extract_topic_word_dist(model_obj):

    print "Extracting topic distributions..."
    topic_x_word = model_obj.m_lambda + model_obj.m_eta #betas in github code
    #Normalizing topics
    topic_x_word = topic_x_word / topic_x_word.sum(1, keepdims=True)

    return topic_x_word

def print_top_n_words( topic_x_word_matrix, vocab_filename, num_words=10 ):
    pass

def main( data_filename, num_emails, vocab_filename, output_prefix ):

    model, ext, txw = train_model( data_filename, num_emails, vocab_filename,
                                   True, True )

    ext.tofile( output_prefix + "_HDP_email_x_topic.npy")
    txw.tofile( output_prefix + "_HDP_topic_x_word.npy")
    model.save( output_prefix + "_HDP_model")

if __name__ == '__main__':
   
    parser = argparse.ArgumentParser(description = __doc__)

    parser.add_argument('data_filename',
        default='data/14453.npy',
        help="Name of data file")
    parser.add_argument('num_emails',
        type=int, default=14453,
        help="Number of emails contained within data file")
    parser.add_argument('vocab_filename',
        default="data/14453_vocab.csv",
        help="Vocabulary file")
    parser.add_argument('output_prefix',
        default='14453',
        help="Prefix for saved output")

    args = parser.parse_args()

    main(args.data_filename,
         args.num_emails,
         args.vocab_filename,
         args.output_prefix)

