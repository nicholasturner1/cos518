#!/usr/bin/python
# -*- coding: utf-8 -*-

import parse_emails as pe
import gensim
import numpy as np
import argparse

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
        for x in range(2,4):
            Grid.columnconfigure(self, x, weight=1)
        Grid.rowconfigure(self, 1, weight=1)
        
        #View Buttons
        #self.createTopicsButton = Button(self, text="Create Topics").grid(row=0,column=0)
        self.topicViewButton    = Button(self, text="Topic View", command=self.displayTopics).grid(row=0, column=0)
        self.socialViewButton   = Button(self, text="Social View").grid(row=0, column=1)
        
        #Topic List
        self.listboxScrollbar = Scrollbar(self, orient=VERTICAL)
        self.listbox = Listbox(self, yscrollcommand=self.listboxScrollbar.set)
        self.listboxScrollbar.config(command=self.listbox.yview)
        self.listboxScrollbar.grid(row=1, column=3, sticky=W+N+S)
        self.listbox.grid(row=1,column=0, columnspan=3, sticky=W+E+N+S)

        
    def displayTopics(self):
        #clear listbox
        self.listbox.delete(0,END)
    
        #Load the topics x word
        topic_x_word = pe.load_topic_x_word('./model_results/round3_LDA_topic_x_word_30.npy', 30)
        #For each topic print the top n words
        word_lists = email_lda.print_top_n_words(topic_x_word, './data/round3_vocab.csv', 10)
        #add these to the display
        for i in range(len(word_lists)):
            self.listbox.insert(END, 'Topic'+ str(i) + ': ' + ', '.join(map(str,word_lists[i])))

        


def main():
  
    root = Tk()
    #root.geometry("400x400")
    app = HomeFrame(root)
    root.mainloop()  


if __name__ == '__main__':
    main()
