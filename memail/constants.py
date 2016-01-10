#!/usr/bin/env python
import os.path

memail_directory = os.path.dirname( os.path.abspath( __file__ ) )
output_prefix = memail_directory + '/user_data/user_gmail'

#========================================
#PARSING CONSTANTS
#Words which occur less than this
# many times are removed from parsing
min_word_count = -1 # = no thresholding

# top n most frequent words
# are removed from parsing
dynamic_stop_thr = 30

# terms which occur in less than
# n docs are removed
term_min_doc_thr = 10

# documents which feature less than
# n remaining terms are removed from
# modeling
doc_min_length_thr = 10

#========================================
#LDA CONSTANTS
#number of initial content topics to learn
num_content_topics = 15
#number of times the model 
# learns from each data point
num_data_passes = 5

#========================================
#DISPLAY CONSTANTS
num_topics_per_email = 3
num_words_per_topic = 10

