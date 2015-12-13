#!/usr/bin/python
# -*- coding: utf-8 -*-

import parse_emails as pe
import gensim
import numpy as np
import argparse
import disp_interface as di
import scipy as sp

from Tkinter import *
import email_lda

def callback():
    print "click!"

class HomeFrame(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")   
        self.parent = parent
        self.initialize()
        
        
    def initialize(self):
        self.parent.title("Simple")
        self.pack(fill=BOTH, expand=1)
        Grid.columnconfigure(self, 2, weight=1)
        Grid.columnconfigure(self, 4, weight=1)
        Grid.rowconfigure(self, 1, weight=1)
        
        #View Buttons
        #self.createTopicsButton = Button(self, text="Create Topics").grid(row=0,column=0)
        self.topicViewButton    = Button(self, text="Topic View", command=self.display_topics).grid(row=0, column=0)
        self.socialViewButton   = Button(self, text="Social View", command=self.display_social).grid(row=0, column=1)
        
        #Email View 
        self.emailText = Text(self)
        self.emailText.grid(row=1, column=4, sticky=W+E+N+S)
        
        #Topic List
        self.listboxScrollbar = Scrollbar(self, orient=VERTICAL)
        self.listbox = Listbox(self, yscrollcommand=self.listboxScrollbar.set)
        
        self.listbox.bind('<<ListboxSelect>>', self.fetch_email)  #uncomment to have selection load an email
        self.listbox.bind('<Double-Button-1>', self.handle_double_click)
        self.listbox.grid(row=1,column=0, columnspan=3, sticky=W+E+N+S)
        
        self.listboxScrollbar.config(command=self.listbox.yview)
        self.listboxScrollbar.grid(row=1, column=3, sticky=W+N+S)
        
        
    def display_topics(self):
    
        self.view_is_category = True
        self.category_is_social = False
        
        #clear listbox
        self.listbox.delete(0,END)

        # Add new topics to display
        topic_x_word = pe.load_topic_x_word('./model_results/round3_LDA_topic_x_word_30.npy', 30)
        word_lists = email_lda.print_top_n_words(topic_x_word, './data/round3_vocab.csv', 10)

        for i in range(len(word_lists)):
            self.listbox.insert(END, 'Topic'+ str(i) + ': ' + ', '.join(map(str,word_lists[i])))
            
    def display_social(self):
    
        self.view_is_category = True
        self.category_is_social = True
    
        #clear listbox
        self.listbox.delete(0,END)
        
        #Load clusters
        social_results_dict = pe.load_social_results_as_dict('./model_results/social_result_raw.mat')
        
        #Find top sender ids in each cluster
        sender_x_social = social_results_dict.get('decomposition_social')
        social_x_sender = sender_x_social.T
        name_list = social_results_dict.get('full_name')
        top_sender_lists = email_lda.print_top_n_people(social_x_sender, name_list, 10)
                
        #Add these top names to listbox
        for i in range(len(top_sender_lists)):
            self.listbox.insert(END, 'Group'+ str(i) + ': ' + ', '.join(map(str,top_sender_lists[i])))
    
    def handle_double_click(self, evt):
        
        if self.view_is_category:
            self.view_is_category = False
            
            if self.category_is_social:
                self.display_emails_for_social(evt)
            
            else:
                self.display_emails_for_topic(evt)
            
        else:
            return


    def display_emails_for_topic(self, evt):
            
        w = evt.widget
        topic_id = w.curselection()[0] #assumes nth row in listbox corresponds to nth topic!
        print 'Displaying emails for topic %i' % topic_id
        
        #Sort emails into their top 3 topics
        ext = pe.load_email_x_topic('./model_results/round3_LDA_email_x_topic_FULL_14453.npy', 14453)
        e_x_sorted_topic = di.assign_emails(ext, 3)
        
        self.cur_topic_emails = []
        #Find email indice that belong in selected topic
        for i in range(len(e_x_sorted_topic)):
            if topic_id in e_x_sorted_topic[i]:
                self.cur_topic_emails.append(i)
                
        #Display email filenames in listbox
        tag_dicts = pe.load_tags('./data/round3_full_tags.csv')
        
        email_subjects = []
        for mail_idx in self.cur_topic_emails:
            email_subjects.append( tag_dicts[mail_idx]['From'].strip() + ' -- ' + tag_dicts[mail_idx]['Subject'].strip() )
        self.listbox.delete(0,END)
        
        for subj in email_subjects:
            self.listbox.insert(END, subj)
            
            
    def display_emails_for_social(self, evt):
            
        w = evt.widget
        cluster_id = w.curselection()[0] #assumes nth row in listbox corresponds to nth topic!
        print 'Displaying emails for social cluster %i' % cluster_id
        
        #Sort emails into their top 3 topics
        e_x_c = sp.io.loadmat('./model_results/social_result_raw.mat').get('decomposition_email')
        e_x_sorted_cluster = di.assign_emails(e_x_c, 3)
        
        self.cur_cluster_emails = []
        #Find email indice that belong in selected topic
        for i in range(len(e_x_sorted_cluster)):
            if cluster_id in e_x_sorted_cluster[i]:
                self.cur_cluster_emails.append(i)
                
        #Display email filenames in listbox
        tag_dicts = pe.load_tags('./data/round3_full_tags.csv')
        
        email_subjects = []
        for mail_idx in self.cur_cluster_emails:
            email_subjects.append( tag_dicts[mail_idx]['From'].strip() + ' -- ' + tag_dicts[mail_idx]['Subject'].strip() )
        self.listbox.delete(0,END)
        
        for subj in email_subjects:
            self.listbox.insert(END, subj)


    def fetch_email(self, evt):
        if self.view_is_category:
            return
            
        w = evt.widget
        #load tags for all mails
        tag_dicts = pe.load_tags('./data/round3_full_tags.csv')        
        self.emailText.delete(1.0,END)
        
        try:
            if self.category_is_social:
                self.emailText.insert(1.0, open('./sarahs_inbox/parsed/msnbc/txt/' + tag_dicts[self.cur_cluster_emails[w.curselection()[0]]]['filename']).read()) 
            else:
                self.emailText.insert(1.0, open('./sarahs_inbox/parsed/msnbc/txt/' + tag_dicts[self.cur_topic_emails[w.curselection()[0]]]['filename']).read()) 
        except:
            print 'Error displaying email (probably none loaded or bad filename)'   
  

def main():
  
    root = Tk()
    #root.geometry("400x400")
    app = HomeFrame(root)
    root.mainloop()  


if __name__ == '__main__':
    main()
