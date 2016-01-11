#!/usr/bin/env python

from sys import argv
from memail import parse_gmails
from memail import email_lda
from memail import frame
from memail import constants
from memail import email_parser
from memail import email_io
import timeit

input_mbox = argv[1]
stats = False
if len(argv) >= 3:
    if argv[2] == '-stats':
        stats = True

#===============================================================================
#Parsing original emails
start_parse = timeit.default_timer() #for stats
    
parse_gmails.main( input_mbox, constants.output_prefix,
                   constants.min_word_count,
                   constants.dynamic_stop_thr,
                   constants.term_min_doc_thr,
                   constants.doc_min_length_thr )
                   
end_parse = timeit.default_timer() #for stats

parser_output_filenames = email_parser.output_filenames( constants.output_prefix ) 

num_emails = email_io.load_num_emails( parser_output_filenames['num_emails'] )
#===============================================================================
#Running LDA model
start_lda = timeit.default_timer() #for stats
email_lda.main( parser_output_filenames['bag_of_words'],
                constants.num_content_topics,
                constants.num_data_passes,
                constants.output_prefix )
 
lda_output_filenames = email_lda.output_filenames( constants.output_prefix,
                                                   num_emails, 
                                                   constants.num_content_topics )

#email_lda.run_inference_over_file( parser_output_filenames['full bag_of_words'],
#                                   lda_output_filenames['model'],
#                                   save=True,
#                                   num_topics=constants.num_content_topics,
#                                   output_prefix=constants.output_prefix )
 
end_lda = timeit.default_timer() # for stats
#===============================================================================
#Building initial inode tree
start_tree = timeit.default_timer()
root = frame.create_gmail_inode_tree( 
                input_mbox,
                parser_output_filenames['vocabulary'],
                lda_output_filenames['email_x_topic'], num_emails,
                lda_output_filenames['topic_x_word'],  constants.num_content_topics )

frame.save_inode_tree(root)
end_tree = timeit.default_timer()

print "MeMail Preparation COMPLETE! (Weeuuw!)"
print "enter 'run-memail.py' in order to view your sorted email"

if (stats):
    print "Email parsing elapsed time:", end_parse - start_parse
    print "LDA modeling elapsed time:", end_lda - start_lda
    print "Tree generation elapsed time:", end_tree - start_tree

