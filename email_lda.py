#!/usr/bin/env python

import parse_emails as pe
import lda

n_topics = 10
n_iter = 2000
random_state = 1

#lda package only accepts count matrices, not tfidf
model = lda.LDA(n_topics=n_topics, 
	n_iter=n_iter, 
	random_state=random_state)

#Loading bag-of-words dataset
m = pe.load_bow_as_dense('data/13999.npy')

#Training LDA model
model.fit(m)

#Saving results
model.doc_topic_.tofile('data/13999_email_x_topic.npy')
model.topic_word_.tofile('data/13999_topic_x_word.npy')