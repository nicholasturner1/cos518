#!/usr/bin/env python

from sys import argv
from memail import parse_gmails
from memail import email_lda
from memail import frame
from memail import constants
from memail import email_parser


input_mbox = argv[1]

num_emails = parse_gmails.num_emails(input_mbox)

#Parsing original emails
parse_gmails.main( input_mbox, constants.output_prefix,
                   constants.min_word_count,
                   constants.dynamic_stop_thr,
                   constants.term_min_doc_thr,
                   constants.doc_min_length_thr )

parser_output_filenames = email_parser.output_filenames( constants.output_prefix ) 


#Running LDA model
email_lda.main( parser_output_filenames['bag_of_words'],
                constants.num_content_topics,
                constants.num_data_passes,
                constants.output_prefix )

lda_output_filenames = email_lda.output_filenames( constants.output_prefix,
                                                   num_emails, 
                                                   constants.num_content_topics )

#Building initial inode tree

