#!/usr/bin/env python

import model_interface as mi
import numpy as np

ext = np.eye(5)

feedback = [

    { 'action' : 'add',    'topic-id' : 0, 'email-id' : 1 },
    { 'action' : 'remove', 'topic-id' : 1, 'email-id' : 1 },
    { 'action' : 'delete', 'topic-id' : 2 },

    #Adding a new topic - should consist of email4
    { 'action' : 'add',    'topic-id' : 5, 'email-id' : 4 },
    { 'action' : 'add',    'topic-id' : 5, 'email-id' : 3 },
    { 'action' : 'remove', 'topic-id' : 5, 'email-id' : 3 },
    
    #Adding a topic and removing it
    { 'action' : 'add',    'topic-id' : 6, 'email-id' : 3 },
    { 'action' : 'delete', 'topic-id' : 6}

]

ext2 = mi.apply_user_feedback( ext, feedback )

print ext2 
