#!/usr/bin/env python
__doc__ = '''
Basic Scheme of using this interface should be the following:

-load a model object from disk
-update it with new examples as need be
-extract state matrices from model object (possibly threaded)
-apply user feedback from record

user feedback is currently assumed to consist of a list
of dictionaries, where each dictionary has at least two fields.

'action' - describes the action to take place
           (one of 'add','remove', or 'delete')
'topic-id' - describes the affected topic for the action

optionally, the dicitonary may also contain another field
'email-id' - describing the email index affected by the action

if the topic id is greater than the maximum index of the topics
defined by the model, this interface will construct a new topic
and append it onto the email_x_topic matrix

NOTE: model-defined topics which are deleted are signified by
zeroing out all email assignments, not explicitly removed from
the model matrices

The module also includes functions for making explicit assignments
of emails to topics given the model state matrices

Also, see TESTS_model_interface.py for examples of feedback schema
'''

import email_io as eio
import email_parser as ep
import email_lda as el

#Dependencies
import gensim
import numpy as np

#=====================================================================
#First, load a model from disk

def load_model(model_filename):
    '''
    Reads a model object from disk along with the model state,
    which contains the topicXword matrix and number of examples
    seen so far
    '''
    model = gensim.utils.SaveLoad.load(model_filename)
    state = gensim.utils.SaveLoad.load(model_filename + '.state')

    model.state = state

    return model

def save_model(model_obj, model_filename):
    '''Saves the model, using the same functionality from the lda script'''
    model_obj.save( model_filename )

 
#=====================================================================
#Apply updates as needed
#(also see update_model_extract_matrices below)


def update_model(email_bow, model_obj):
    '''
    Takes a new bow matrix and updates the model using
    the new data
    '''
    
    email_corpus = gensim.matutils.Dense2Corpus(email_bow,
                                    documents_columns=False)

    model_obj.update(email_corpus)

    return model_obj


def add_new_emails(email_texts, other_bow, vocab_index, model_obj):
    '''
    Takes a list of new email message bodies, updates the model
    with the new data, and adds the new bow vectors to the previous
    bow matrix
    '''
    
    email_bow = ep.map_text_to_bow(email_text, vocab_index=vocab_index, dense=True)

    new_model = update_model(email_bow, model_obj)

    new_bow = np.append(other_bow, email_bow, axis=0)
 
    return new_model, new_bow

#=====================================================================
#Extract model-derived state matrices


#Main interface function
def update_model_extract_matrices(email_texts, other_bow, vocab_index, model_obj):
    '''
    Updates the model with new data, returns the new bow matrix, model state, 
    and state matrices
    '''

    new_model, new_bow = add_new_email(email_texts, other_bow, vocab_index, model_obj)

    ext, txw = extract_state_matrices(new_model, new_bow)

    return new_model, new_bow, ext, txw


def extract_state_matrices(model_obj, bow):
    '''
    Pulls the matrices describing the state of the model
    out of the object
    '''

    new_corpus = gensim.matutils.Dense2Corpus( bow,
                                    documents_columns=False )

    #Running inference over the corpus can take some
    # time, may be more useful running in a thread
    ext = run_inference(model_obj, new_corpus)
    txw = extract_topic_word_dist(model_obj)

    return ext, txw


#=====================================================================
#Replay user feedback


def apply_user_feedback(emailXtopic, topicXword, feedback):
    '''
    Applies feedback actions to the supplied matrices

    Feedback is assumed to consist of a list of dictionaries,
    which have a specific structure defined in the module's doc string

    Feedback is also assumed to follow chronological order, and will
    ignore references to missing topics, etc.
    '''

    num_model_defined_topics = emailXtopic.shape[1]
    user_defined_topics = {}
    
    #first, we apply all modifications to model-defined topics
    apply_model_defined_feedback(emailXtopic, feedback)

    #then we define the user's topics based on the most recent
    # version of the model-defined topics

    #compiling which emails contribute to which new topics
    new_topics = compile_user_defined_topics(emailXtopic, feedback)

    #creating the user defined topics, and adding to the eXt matrix
    emailXtopic, topicXword = add_user_defined_topics( 
                                  emailXtopic, 
                                  topicXword, 
                                  new_topics ) 

    return emailXtopic, topicXword

    
def apply_model_defined_feedback(emailXtopic, feedback):
    '''Applies feedback actions based on model-defined topics'''

    num_model_defined_topics = emailXtopic.shape[1]

    for choice in feedback:

        if choice['topic-id'] >= num_model_defined_topics:
            continue
 
        if choice['action'] == 'add':
            add_email_to_model_topic(emailXtopic,
                               choice['email-id'],
                               choice['topic-id'])

        elif choice['action'] == 'remove':
            remove_email_from_model_topic(emailXtopic,
                               choice['email-id'],
                               choice['topic-id'])

        elif choice['action'] == 'delete':
            delete_model_topic(emailXtopic,
                               choice['topic-id'])


def compile_user_defined_topics( emailXtopic, feedback ):
    '''
    Consolidates across chronologically ordered actions to
    find the email ids which contribute to a user-defined topic
    '''

    user_defined_topics = {}
    num_model_defined_topics = emailXtopic.shape[1]
    
    for choice in feedback:
        
        if choice['topic-id'] < num_model_defined_topics:
            continue

        if choice['action'] == 'add':
            user_defined_topics = add_email_to_user_topic(user_defined_topics,
                                                          choice['email-id'],
                                                          choice['topic-id'])

        if choice['action'] == 'remove':
            user_defined_topics = remove_email_from_user_topic(user_defined_topics,
                                                          choice['email-id'],
                                                          choice['topic-id'])

        if choice['action'] == 'delete':
            user_defined_topics = delete_user_topic(user_defined_topics,
                                                    choice['topic-id'])


    return user_defined_topics


def add_user_defined_topics( emailXtopic, topicXword, user_defined_topics ):
    '''
    Makes new topics according to the seed email structure, and 
    adds the new email distributions to the eXt matrix
    '''

    #initializing new email distributions to add
    num_emails = emailXtopic.shape[0]
    num_words  = topicXword.shape[1]
    num_new_topics = len(user_defined_topics)

    ext_new = np.empty((num_emails, num_new_topics), dtype=emailXtopic.dtype)
    txw_new = np.empty((num_new_topics, num_words), dtype=topicXword.dtype)

    for index, topic_id in enumerate( sorted(user_defined_topics.keys()) ):

        ext_new[:,index], txw_new[index,:] = make_new_topic( emailXtopic, 
                                                 topicXword,
                                                 user_defined_topics[topic_id] )

    #np.append is slow, so we create all the topics before 
    # adding them to the eXt matrix in one call
    full_ext = np.append( emailXtopic, ext_new, axis=1 )
    full_txw = np.append( topicXword , txw_new, axis=0 )
    return full_ext, full_txw

def make_new_topic( emailXtopic, topicXword, email_id_list ):
    '''
    Current scheme is to generate a new topic
    by averaging the topic distribution of seed emails,
    and projecting all emails onto that axis
    '''
    num_topics = emailXtopic.shape[1]
    num_email_ids = len(email_id_list)

    #init
    topic_dist = np.zeros((num_topics,), dtype=emailXtopic.dtype)

    for email_id in email_id_list:

        topic_dist += emailXtopic[email_id,:]

    avg_topic_dist = topic_dist / num_email_ids

    #projecting emails onto average topic distribution
    # of seeds
    email_dist = emailXtopic.dot(avg_topic_dist)
    email_dist = email_dist / np.sum(email_dist) #norm

    word_dist = topicXword.transpose().dot(avg_topic_dist)
    word_dist = word_dist / np.sum(word_dist)

    return email_dist, word_dist


def add_email_to_model_topic(emailXtopic, email_index, topic_index):
    '''
    Guarantees that an email is sorted into a given topic unless
    the email is assigned by the user to more than the topic display
    count
    '''
    #model-derived topic weights are normalized to [0,1], 
    # so 1 is the highest possible weight
    emailXtopic[email_index, topic_index] = 1


def add_email_to_user_topic(user_defined_topics, email_index, topic_index):
    '''Adds a seed email to a user-defined topic'''

    if user_defined_topics.has_key(topic_index):
        user_defined_topics[topic_index].append( email_index )

    else:
        user_defined_topics[topic_index] = [email_index]

    return user_defined_topics


def remove_email_from_model_topic(emailXtopic, email_index, topic_index):
    '''
    Guarantees that an email is not sorted into a given topic
    unless almost all other options are exhausted as well (deviant user behavior)
    '''
    emailXtopic[email_index, topic_index] = 0


def remove_email_from_user_topic(user_defined_topics, email_index, topic_index):
    '''Removes a seed email from a user-defined topic'''

    if user_defined_topics.has_key(topic_index):

        try:
          user_defined_topics[topic_index].remove(email_index)
        except ValueError:
          pass

    else:        
        pass

    return user_defined_topics


def delete_model_topic( emailXtopic, topic_id ):
    '''
    Signifies that this topic should not be displayed
    by zeroing out all email assignments
    '''
    emailXtopic[:, topic_id] = 0


def delete_user_topic( user_defined_topics, topic_index ):
    '''Removes a user topic from the creation process'''

    try:
        del user_defined_topics[topic_index]
    except KeyError:
        pass

    return user_defined_topics


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

#=====================================================================
#Assignment Functions (originally within disp_interface.py)

def assign_topic( email_x_topic_matrix, num_ids):
    return column_cluster_ids( email_x_topic_matrix, num_ids )

def assign_emails( email_x_topic_matrix, num_ids):
    return row_cluster_ids( email_x_topic_matrix, num_ids )

def row_cluster_ids( assign_matrix, num_ids ):
    '''
    Takes a matrix which makes a soft assignment of rows to 
    a cluster (either content topic or social topic) and returns
    an explicit hard assignment of each row to a {num_ids} number
    of clusters
    '''

    rows, cols = assign_matrix.shape
    
    assignments = []

    for i in range(rows):
        row_assignment = np.argsort( assign_matrix[i,:] )[::-1][:num_ids]
        assignments.append( row_assignment )

    return assignments



def column_cluster_ids( assign_matrix, num_ids ):
    '''
        Takes a matrix which makes a soft assignment of column to
        a cluster (either content topic or social topic) and returns
        an explicit hard assignment of each column to a {num_ids} number
        of clusters
        '''
    
    rows, cols = assign_matrix.shape
    
    assignments = []
    
    for i in range(cols):
        col_assignment = np.argsort( assign_matrix[:,i] )[::-1][-num_ids:]
        assignments.append( col_assignment )
    
    return assignments
