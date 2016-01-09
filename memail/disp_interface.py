#!/usr/bin/env python

import numpy as np


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
