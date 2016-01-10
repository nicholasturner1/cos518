from dateutil.parser import parse as date_parser
import thread
import threading
import email_io as eio
import numpy as np
import disp_interface as di
from scipy import io
from ttk import *
from Tkinter import *
import tkFont
import ttk
import email as em
import imaplib
import pickle
import os
import tkMessageBox
import os.path
import glob
import email_lda
from time import gmtime, strftime
import hashlib
import tkFont
from PIL import Image, ImageDraw
from multiprocessing.pool import ThreadPool
import random
import model_interface as mi
import parse_gmails as pg
import email_parser as ep
import mailbox
import social as soc
from Dialog import Dialog
import time
import constants


buffer_size = 5000
buffer_time = 0.05

wait_time = 20
Active_Thread = []


################################################################################################
#CONSTANTS

NUM_TOPICS_PER_EMAIL = 3

################################################################################################
#route
TYPE = ["root", "email", "directory", "unknown", "sub_root"]
real_path = os.path.dirname(os.path.realpath(__file__))
save_file = os.path.dirname(os.path.realpath(__file__)) + '/saved_file/saved_file'
log_file = os.path.dirname(os.path.realpath(__file__)) + '/log_file/server_log'
temp_save_file= os.path.dirname(os.path.realpath(__file__)) + '/saved_file/temp_saved_file'
################################################################################################
#write to disk
class disk_writer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.buffer = ''
        self.time = time.clock()
        self.log_file = open(real_path + '/log_file/log', 'w')
    
    def run(self):
        
        if len(self.buffer) > buffer_size or time.clock() - self.time > buffer_time:

            log_file = open(real_path + '/log_file/log', 'w')
            log_file.write(self.buffer)
            log_file.close()
            buffer = ''
            self.time = time.clock()

#tk.after(1000, self.run, )


_disk_writer = disk_writer()



################################################################################################
#font
num_directory_words = 35
all_column = 7
current_location_font = ('Apple Chancery', '13')
email_font = ('Apple Causal', '12')
email_title_font = ('Georgia', '15', 'bold')
title_text_font = ('Zapfino', '10')
title_info_font = ('Georgia', '15')
title_date_font = ('pligy', '15')
directory_font = ('Apple Causal', '12', 'bold')
description_font = ('Apple Causal', '12')
left_option_font = ('Krungthep', 15)
option_one_font = ('Copperplate', 14)
search_font = ('Futura', '14')


################################################################################################
#color


information_color = 'grey85'
separator_color = 'light grey'
separator_dark = 'grey40'
separator_mid = 'grey60'
side_color = 'grey93'
separator_huge_height = 4
#helv20 = tkFont.Font(family="Helvetica",size=20,weight="bold")

save_file_short = 'temp_saved_file'

################################################################################################
#data structure, email: sender, to, title, date, email, vec
#id: type + number, type: u(unknown), R(root), r(sub root), t(topic), s(social), e(email)
class inode:
    def __init__(self, parents = [], children = [], name = "New Entry", description = "" , type = "unknown", email_directory = "", email = [], id = [], vec = [], ext = []):
        self.parents = parents
        self.children = children
        self.name = name
        self.type = type
        self.description = description
        self.email_directory = email_directory
        self.email = email
        self.hash = 0
        self.vec = vec
        self.ext = ext
        self.sorted_chronologically = True
        if len(id) >= 2:
            self.id = id
        elif len(id) == 1:
            self.id = id +  str(int(random.random()*10000000))
        else:
            self.id = 'u' + str(int(random.random()*10000000))
        
        self.code = str(int(random.random()*10000000))
        #ML Result Matrices for sub_root inodes
        self.email_x_group = []      #group = topic or social cluster
        self.group_x_individual = [] #individual = word or person


    def hash(self, inode):
        #print inode
        m = hashlib.md5()
        m.update(inode.name)
        m.update(inode.description)
        m.update(inode.type)
        m.update(inode.email_directory)
        for entry in inode.email:
            for item in entry:
                m.update(item)
        if not inode.children:
            return m.hexdigest()
        else:
            child_hash = []
            for child in inode.children:
                child_hash.append(child._hash())
            child_hash = sorted(child_hash, key = lambda x: x.lower(), reverse = True)
            child_hash = "-".join(child_hash)
            m.update(child_hash)
            return m.hexdigest()

################################################################################################

class test_frame(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        
        event_handler = self
        
        ######################################################################################
        #key
        master.bind("<Key>", self.detect_key)
        
        
        ######################################################################################
        #config
        
        
        option_one = option_one_frame(self, event_handler)
        #option_one.pack()
        #option_one.place(height = 200, width = 500)
        option_one.grid(row = 1, column = 1, columnspan = 6, sticky = EW)
        load_info = load_info_frame(self)
        load_info.grid(row = 1, column = 7, columnspan = 1, sticky = EW)
        
        option_two = option_two_frame(self, event_handler)
        option_two.grid(row = 2, column = 1, columnspan = 7, sticky = EW)
        
        
        current_location = current_location_frame(self, event_handler)
        current_location.grid(row = 3, column = 1, columnspan = 7, sticky = EW)
        self.current_location = current_location.current_location;
        _search_frame = search_frame(self, event_handler)
        _search_frame.grid(row = 3, column = 7, columnspan = 4, sticky = EW)
        
        #f = Frame(self, height = 1, bg = separator_color)
        f = ttk.Progressbar(self, orient='horizontal', mode='determinate', style="TProgressbar")
        f.grid(row = 4, column = 1, columnspan = all_column, sticky = EW)
        self.pb = f
        
        left_option = left_option_frame(self, event_handler)
        left_option.grid(row = 5, column = 1, rowspan = 10, sticky = NS)
        
        
        
        self.top_directory = top_directory_frame(self, event_handler, root.children)
        self.top_directory.grid(row = 5, column = 3, rowspan = 2, sticky = NW)
        #self.directories = top_directory.directory
        
        f = Frame(self, width = 1, bg = separator_color)
        f.grid(row = 5, column = 4, rowspan = 2, sticky = NS)
        
        f = Frame(self, width = 1, bg = separator_color)
        f.grid(row = 5, column = 2, rowspan = 2, sticky = NS)
        
        email_f = email_frame(self, event_handler)
        email_f.grid(row = 5, column = 5, columnspan = 3, sticky = N)
        
            
        
        
        ######################################################################################
        #config
        try:
            os.remove(real_path + '/log_file/log')
        except OSError:
            x = 0
        
        self.inode_map = {}

        self.log_file = open(real_path + '/log_file/log', 'w')
        self.loading = False
        self.shift_down = False
        self.email = email_f
        self.keywords = email_f.keywords
        self.master = master
        self.root = root
        self.directory = root
        self.directory_back_up = self.directory
        self.temp_directory = []
        self.temp_frame = []
        self.directory_stack = [root]
        self.topic_folder = root.children[0]
        self.social_folder = root.children[1]
        self.unsorted_email_folder = root.children[2]
        #root.children.append(self.unsorted_email_folder)
        self.load_directory()
        self.search_directory = inode(parents = [root], children = [], type = "sub_root", name = "Search Results")

    ##########################################################################################
    #key event
    def detect_key(self, event):
        x = 0
        #print "gg"
        #if (event.keycode == 131330 or event.keycode == 131074) and event.state == 1:
        #    self.shift_down = True
        # print "here"
        # if event.keycode == 1048584 and event.state == 8:
        #     self.shift_down = False
        
        #print "Keycode:", event.keycode, "State:", event.state
    ##########################################################################################
        
    def change_current_location(self):
        self.current_location.configure(state = 'normal')
        self.current_location.delete(1.0, END)
        location = ""
        for directory in self.directory_stack:
            location = location + "/" + directory.name
        self.current_location.insert(END, location)
        self.current_location.configure(state = 'disabled')
   
    ##########################################################################################
    #selection
    def select_directory(self, select_frame, select_directory, shift_down):

        if not shift_down:

            if self.temp_frame:
                for frame in self.temp_frame:
                    frame.normal_color()
        
            select_frame.deep_color()
            self.temp_frame = [select_frame]
            self.temp_directory = [select_directory]

        else:
            select_frame.deep_color()
            self.temp_frame.append(select_frame)
            self.temp_directory.append(select_directory)
        
        
        
        
        if len(self.temp_directory) == 1 and self.temp_directory[0].type == "directory":
            change_text_field(self.keywords, self.temp_directory[0].description)


    def click_directory(self, select):
    
        if select.type == "email":
            self.load_email(select)
        else:
            self.directory = select
            self.directory_stack.append(self.directory)
            self.load_directory()
            self.current_location.configure(state='normal')
            self.current_location.delete(1.0, END)
            self.current_location.insert(END, select.description)
            self.current_location.configure(state='disabled')
            self.change_current_location()
    ##########################################################################################
    #load and sort

    def load_email(self, inode):
        
        _email = inode.email
        if not _email:
            _email = self.read_email_text(inode.email_directory)
        #print email_text
        try:
            change_text_field(self.email.email_text, _email['email'])
            change_text_field(self.email.sender, _email['sender'])
            change_text_field(self.email.to, _email['to'])
            change_text_field(self.email.title, _email['title'])
            change_text_field(self.email.date, _email['date'])
        except:
            return
    
    def load_directory(self):
        
        children = self.directory.children
        self.top_directory.grid_forget()
        self.top_directory = top_directory_frame(self, self, children)
        self.top_directory.grid(row = 5, column = 3, sticky = NW)

    def sort(self, event):
        children = self.directory.children
        children = self.sort_children(children)
        self.top_directory.grid_forget()
        self.top_directory = top_directory_frame(self, self, children)
        self.top_directory.grid(row = 5, column = 3, sticky = NW)
    
    def sort_children(self, children):
        if children[0].type != "email":
            return children
        
        #load the email contents for sorting purposes
        for child in children:
            if not child.email:
                child.email = self.read_email_text(child.email_directory)

        
        #sort emails based on dropdown
        #dropdown = 0 #not really a dropdown yet

        #toggled sort between chrono and topic
        #if dropdown == 0: #sort by date
        if not self.directory.sorted_chronologically:
            sorted_children = sorted(children, key=lambda x: str(x.email['date']).lower(), reverse=True)

            self.directory.sorted_chronologically=True

        #elif dropdown == 1: #sort by subject
            #sorted_children = sorted(children, key=lambda x: x.email['title'].lower(), reverse=False)

        else:
        #elif dropdown == 2: #sort by topic proportion
	    topic_directories = self.directory.parents[0].children
	    topic_index = [i for i in range(len(topic_directories)) 
			     if topic_directories[i] == self.directory][0] 

            sorted_children = sorted(children, key=lambda x: x.vec[topic_index], reverse=True)
            
            self.directory.sorted_chronologically=False
        #else:
        #    sorted_children = children

        return sorted_children
        
    ##########################################################################################
    #jumps
    def back(self, event):
        if self.directory.type == "root":
            return
        else:
            self.directory_stack.pop()
            new_directory  = self.directory_stack.pop()
            self.directory_stack.append(new_directory)
            self.directory = new_directory
            self.change_current_location()
            self.load_directory()

    def back_to_unsorted(self, event):
        new_directory  = self.unsorted_email_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = [new_directory]
        self.change_current_location()
        self.load_directory()

    def back_to_social(self, event):
        new_directory  = self.social_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = [new_directory]
        self.change_current_location()
        self.load_directory()
        
    def back_to_topic(self, event):
        new_directory  = self.topic_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = [new_directory]
        self.change_current_location()
        self.load_directory()


    ##########################################################################################
    #read email
    def read_email_text(self, filename):
        with open(filename) as f:
            lines = f.readlines()
            lines = [line.split('\n')[0] for line in lines]
            lines = [line.decode('utf-8',errors='ignore') for line in lines]
        f.close()
        _email = ''
        sender = ''
        to = ''
        title = ''
        date = ''
        #sender
        sender_fieldnames = ['From', 'Frorn']
        for fieldname in sender_fieldnames:
            sender_line = [line for line in lines if fieldname in line]
            for senders in sender_line:
                if not sender:
                    ind = senders.find(fieldname)
                    sender = senders[ind + 6:-1].strip()
                    lines = [line for line in lines if senders not in line]
        #sender = sender.replace(" ", "")
        
        to_fieldnames = ['To', 'to']
        for fieldname in to_fieldnames:
            to_line = [line for line in lines if fieldname in line]
            for tos in to_line:
                if not to:
                    ind = tos.find(fieldname)
                    to = tos[ind + 4:-1].strip()
                    lines = [line for line in lines if tos not in line]

        title_fieldnames = ['Subject', 'subject']
        for fieldname in title_fieldnames:
            title_line = [line for line in lines if fieldname in line]
            for titles in title_line:
                if not title:
                    ind = titles.find(fieldname)
                    title = titles[ind + 9:-1].strip()
                    lines = [line for line in lines if titles not in line]

        date_fieldnames = ['Sent', 'sent']
        for fieldname in date_fieldnames:
            date_line = [line for line in lines if fieldname in line]
            for dates in date_line:
                if not date:
                    ind = dates.find(fieldname)
                    date = dates[ind + 5:-1].strip()
                    lines = [line for line in lines if dates not in line]
    
            #sender = sender_line[0]
        metadata_fieldnames = ['Searchable', 'Unknown', 'Page']
        for fieldname in metadata_fieldnames:
            lines = [line for line in lines if fieldname not in line]
    #metadata_fieldnames = ['Date:','To:','From:','Subject:','Sent:','Cc:','Attachments:','Recipients:','Importance:','Sender:','Bcc:']
        start = False
        for line in lines:
            if len(line) <= 1 and start == False:
                x = 1
            else:
                _email = _email + line + '\n'
                start = True
                    #date.strip()
    
        if not date:
            return {'email': _email, 'sender': sender, 'to': to, 'title': title, 'date': date}
        if len(date) < 8:
            return {'email': _email, 'sender': sender, 'to': to, 'title': title, 'date': date}

        date = date.replace(":", "")
        date = date.replace(";", "")
        date = date.replace("_", "")
        date = date.replace("PM", "P")
        date = date.replace("AM", "A")
        date = date.replace(".A", " A")
        date = date.replace(".P", "P ")
        date = date.replace(". P", " P")
        date = date.lstrip()
        try:
            date = date_parser(date)
        except:
            date = date[:-4] + ':' + date[-4:]
        
            try:
                date = date_parser(date)
            except:
               
                date1 = date[:-7] + ' ' + date[-7:]
                try:
                    date = date_parser(date1)
                except:
                    try:
                        date = date[:-6] + ' ' + date[-6:]
                        date = date_parser(date)
                    except:
                        #print date
                        date = "0000-00-00 00:00:00"



        return {'email': _email, 'sender': sender, 'to': to, 'title': title, 'date': date}
    ##########################################################################################
    #search
    def all_emails(self, root):
        directory_root = root
        queue = [directory_root]
        visited = set()
        count = 0
        inode_set = []
        while queue:
            temp_root = queue.pop(0)
            if temp_root not in visited:
                inode_set.append(temp_root)
                count = count + 1
                visited.add(temp_root)
                for child in temp_root.children:
                    queue.append(child)
    
        for item in inode_set:
            if not (item.type == "email" and len(item.email) > 0):
                inode_set.remove(item)
        
        return inode_set
                    
    def search(self, keywords):
        if self.directory == self.search_directory:
            self.directory = self.directory_back_up
            self.directory_stack.pop()
        emails = self.all_emails(self.directory)
        #print emails
        self.search_directory.children = []
        self.directory_back_up = self.directory
        self.directory = self.search_directory
        for email in emails:
            if not len(email.email) == 0:
                position  = email.email['email'].find(keywords)
                if not position == -1:
                    #print position, email
                    self.directory.children.append(email)
        self.load_directory()
        self.directory_stack.append(self.search_directory)
        self.change_current_location()
    
    
    ##########################################################################################
    #insertion and deletion
    def _insert(self, root, inode):
        self.inode_map[inode.id] = inode
        _add(inode, root)
        #print "i " + str(root.id) + "," + str(inode.id)
    
    def insert_entry(self, event):
        if self.directory == self.search_directory:
            return
        self._pop_up_insert = pop_up_insert(self.master)
        self.master.wait_window(self._pop_up_insert.top)
        if self._pop_up_insert.value:
            if self.directory == self.topic_folder:
                self._insert(self.directory, inode(name = self._pop_up_insert.value, parents = [self.directory], children = [], type = "directory", id = 't'))
            if self.directory == self.social_folder:
                self._insert(self.directory, inode(name = self._pop_up_insert.value, parents = [self.directory], children = [], type = "directory", id = 's'))
            #self.temp_directory.name = self._pop_up_insert.value;
            self.load_directory()



        #print "d " + str(root.id) + "," + str(inode.id)
    
    def delete_entry(self, event):
        if self.directory == self.search_directory:
            directory = self.directory_back_up
        else:
            directory = self.directory
        if not self.temp_directory:
            return
        if self.temp_directory[0].type == "sub_root" or self.temp_directory[0].type == "root":
            return
        self._pop_up_delete = pop_up_delete(self.master)
        self.master.wait_window(self._pop_up_delete.top)
        
        if self._pop_up_delete.delete:
            for temp_directory in self.temp_directory:
                _delete(directory, temp_directory, self.unsorted_email_folder)
                #self._remove(temp_directory, directory)
                _remove(temp_directory, self.search_directory)
    #self.load_directory()
    ##########################################################################################
    #rename

    def rename_entry(self, event):
        if not (len(self.temp_directory) == 1 and len(self.temp_frame) == 1):
            return
        
        temp_directory = self.temp_directory[0]
        temp_frame = self.temp_frame[0]
        if not (temp_directory.type == "directory" or temp_directory.type == "email"):
            return
        self._pop_up_rename = pop_up_rename(self.master)
        self.master.wait_window(self._pop_up_rename.top)
        new_name = self._pop_up_rename.name
        new_name = new_name.replace('#', '')
        new_name = new_name.replace(':', '')
        if new_name:
            change_text_field(temp_frame.line_one, new_name)
            self._rename(temp_directory, new_name)
    ##########################################################################################
    #add and move entry
    def _move(self, old_root, new_root, inode):
        _remove(inode, old_root)
        _add(inode, new_root)
        #print "m " + str(old_root.id) + "," + str(new_root.id) + ","+ str(inode.id)

    def _add_(self, root, inode):
        _add(inode, root)
        #print "a " + str(root.id) + ","+ str(inode.id)


    def move_entry(self, event):
        
        if not self.temp_directory:
            return
        if not self.temp_directory[0].type == "email":
            return
        
        self._pop_up_move = pop_up_move(self.master, self.root)
        self.wait_window(self._pop_up_move.top)
        if self._pop_up_move.select_inode:
        #print "here"
            parent = self.directory
            if parent == self.search_directory:
                parent = self.directory_back_up
        
            for temp_directory in self.temp_directory:
                temp_directory.children = []
                self._move(parent, self._pop_up_move.select_inode, temp_directory)
                #self._remove(temp_directory, parent)
                #self._add(temp_directory, self._pop_up_move.select_inode)
            
            self.load_directory()

    def add_entry(self, event):
        if not self.temp_directory:
            return
        if not self.temp_directory[0].type == "email":
            return
        
        self._pop_up_move = pop_up_move(self.master, self.root)
        self.wait_window(self._pop_up_move.top)
        if self._pop_up_move.select_inode:
            #print "here"
            parent = self.directory
            if parent == self.search_directory:
                parent = self.directory_back_up
            for temp_directory in self.temp_directory:
                temp_directory.children = []
                _add(self._pop_up_move.select_inode, temp_directory)

            
            self.load_directory()
    ##########################################################################################
    #modify inde
    def _rename(self, inode, name):
        old_name = inode.name
        inode.name = name
        _disk_writer.buffer =  _disk_writer.buffer + "r:" + str(inode.id) + '#' + str(inode.code) + ":" + name + '#' + old_name + '\n'


    def _remove(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            return
        try:
            child.parents.remove(parent)
        except ValueError:
            pass
        if parent == self.search_directory:
            return
    #print "d " + str(child.id) + "," + str(parent.id)

        _disk_writer.buffer =  _disk_writer.buffer + "d:" + str(child.id)+ '#' + str(child.code)  + ":" + str(parent.id) +  '#' + str(parent.code)+ '\n'
    def _remove_without_log(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            pass
        try:
            child.parents.remove(parent)
        except ValueError:
            pass


    def _add(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            pass
        parent.children.insert(0, child)
        try:
            child.parents.remove(parent)
        except ValueError:
            pass
        child.parents.insert(0, parent)
        _disk_writer.buffer =  _disk_writer.buffer + "a:" + str(child.id)+ '#' + str(child.code)  + ":" + str(parent.id) +  '#' + str(parent.code)+ '\n'

    def _add_without_log(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            pass
        parent.children.insert(0, child)
        try:
            child.parents.remove(parent)
        except ValueError:
            pass
        child.parents.insert(0, parent)

#print "a " + str(child.id) + "," + str(parent.id)

    ##########################################################################################
    #log in, load new emails
    def login_window(self, event):
        self._pop_up_log_in = pop_up_log_in(self.master)
        self.master.wait_window(self._pop_up_log_in.top)
        if self._pop_up_log_in.username:
            self.login(self._pop_up_log_in.username, self._pop_up_log_in.password)
    
    def login(self, username, password):
        '''Logs user into gmail, loads emails into unsorted email folder'''
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(username, password)
        mail.list()
        inbox = mail.select("inbox") # connect to inbox.
        result, data = mail.search(None, "ALL")
        ids = data[0] # data is a list.
        id_list = ids.split() # ids is a space separated string
        
        #clean box
        self.topic_folder.children = [];
        self.social_folder.children = [];
        self.unsorted_email_folder.children = [];
       
        #get emails
        for id in id_list:
            result, data = mail.fetch(id, "(RFC822)")
            [sender, to, title, date, body] = self.parse_email_remote(data[0][1])

            child = inode(parents = [self.unsorted_email_folder], name = sender[0], description = title, email = {'email': body, 'sender': sender, 'to':to, 'title': title, 'date': date}, children = [], type = "email")
            self.unsorted_email_folder.children.append(child)



    def parse_email_remote(self, raw_email):
        '''Parses data from remote gmail email'''
        email_message = em.message_from_string(raw_email)
        to =  email_message['To']
        sender = em.utils.parseaddr(email_message['From'])
        title = email_message['Subject']
        date = email_message['Date']
        b = em.message_from_string(raw_email)
        body = ""

        if b.is_multipart():
            for part in b.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
        
                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True)  # decode
                    break
        else:
            body = b.get_payload(decode=True)

        try:
            date = date_parser(date)
        except:
            print date
        email = body
        return [sender, to, title, date, body]
    ##########################################################################################
    #save and load
    def save(self, event):
        if self.loading:
            tkMessageBox.showinfo("Still Loading...", "Please wait loading to finish before saving...")
        else:
            ans = Dialog(self,title   = 'Options',text    = 'Save to local or server?', bitmap  = 'questhead', default = 0, strings = ('Local', 'Server', 'Cancel'))
            if ans.num == 0:
                _info_session = info_session(self)
                thread.start_new_thread(save_thread, (self, _info_session,))
            if ans.num == 1:
                thread.start_new_thread(save_server, (self, ))
    
    #load
    def load(self):
        ans = Dialog(self,title   = 'Options',text    = 'Load from local or server?', bitmap  = 'questhead', default = 0, strings = ('Local', 'Server', 'Cancel'))
        if ans.num == 0:
            self.loading = True
            thread.start_new_thread ( load_thread, (self,))
        if ans.num == 1:
            self.loading = True
            thread.start_new_thread ( self.reconstruct_thread, ())
    
    


    def consistent_load(self, event):
        ans = Dialog(self,title   = 'Options',text    = 'Load from local or server?', bitmap  = 'questhead', default = 0, strings = ('Local', 'Server', 'Cancel'))
        if ans.num == 0:
            self.loading = True
            _info_session = info_session(self)
            lgi = _load_email_(self, "local_email", _info_session)
            lgi.start()
        if ans.num == 1:
            self.loading = True
            _info_session = info_session(self)
            thread.start_new_thread ( self.reconstruct_thread, ( _info_session,))

    def consistent_load2(self, event):
        all_files = glob.glob(save_file + '*')
        all_files = sorted(all_files, key=lambda x: x.lower(), reverse=True)
        #print all_files
        if all_files:
            #print "load from file: " + all_files[0]
            f = open(all_files[0])
            inode_set = pickle.load(f)
            f.close()
            root = inode_set[0]
            if not consistency_check(root, self.root):
                if not tkMessageBox.askokcancel("Conflict!", "Override or not?..."):
                    return
            self.root = root
            self.directory = root
            self.temp_directory = [root]
            self.temp_frame = []
            self.directory_stack = [root]
            self.topic_folder = root.children[0]
            self.social_folder = root.children[1]
            self.unsorted_email_folder = root.children[2]
    #root.children.append(self.unsorted_email_folder)
        self.load_directory()


##########################################################################################
    def load_gmail_inbox(self, event):
#thread.start_new_thread(load_gmail_inbox_thread, (self, ))
        _info_session = info_session(self)
        lgi = _load_email_(self, "gmail", _info_session)
        lgi.start()
    ##########################################################################################
    #reconstruct from a log file
    def reconstruct_event(self, event):

        self.reconstruct('log2')

    def reconstruct_thread(self, _info_session):
        all_files = glob.glob(log_file + '*')
        all_files = sorted(all_files, key=lambda x: x.lower(), reverse=False)
        _info_session.new_message = "Loading from server..."
        if not all_files:
            _info_session.destory()
            return
        for file in all_files:
            print file
            self.reconstruct(file, _info_session)
            os.remove(file)
        _info_session.destory()
        self.loading = False
    #return
    
    def reconstruct(self, file, _info_session):
        log_file = open(file)
        lines = log_file.readlines()
        log_file.close()
        count = 0
        for line in lines:
            count = count + 1
            _info_session.new_message = "Loading from server...line " + str(count) + "(out of" + str(len(lines)) + ")"
            instruction, child, target = self._parse_log(line)
            child_id = child[0]
            child_code = child[1]
            target_id = target[0]
            target_code = target[1]
            try:
                inode = self.inode_map[str(child_id)]
                if instruction == 'r':
                    self._rename(inode, target_id)
                else:
                    try:
                        parent = self.inode_map[str(target_id)]
                    except:
                        self._inconsistent(line)
                #return
                    if instruction == 'a':
                        _add(inode, parent)
                    if instruction == 'd':
                        _remove(inode, parent)
            except:
                self._inconsistent(line)
                #return
        



    def _parse_log(self, line):
        result = line.split(':')
        instruction = result[0]
        child = result[1].split('#')
        target = result[2].replace('\n', '').split('#')
        return instruction, child, target

    def _inconsistent(self, id):
        #print self.inode_map
        print 'inconsistent! ' +  id
    ##########################################################################################
    #social training:
    def social_training(self):
        inode_set = self.all_emails(self.root)
        exs, descriptions = soc.social_clustering(inode_set, num_cluster = 20)
        self.reconstruct_social(exs, descriptions)

    ##########################################################################################
    #apply user feedbacks:
    def user_feedback_event(self, event):
        _info_session = info_session(self)
        thread.start_new_thread(self.user_feedback, ('log', _info_session))

    def user_feedback(self, file, _info_session):
        #reconstruct topic

        log_file = open(real_path + '/log_file/' + file)
        lines = log_file.readlines()
        log_file.close()
        feedback = []
        _info_session.new_message = "reading log..."
        for line in lines:
            instruction, child, target = self._parse_log(line)
            child_id = child[0]
            target_id = target[0]
            try:
                inode = self.inode_map[str(child_id)]
            except:
                self._inconsistent(line)
                return

            
            if not instruction == 'r':
                try:
                    parent = self.inode_map[str(target_id)]
                except:
                    self._inconsistent(line)
                    return
                if instruction == 'a' and parent.id[0] == 't' and inode.id[0] == 'e':
                    
                    feedback.append({'action' : 'add',    'topic-id' : int(parent.id[1:]), 'email-id' : str(inode.id[1:])})
                if instruction == 'd' and inode.id[0] == 't':
                    feedback.append({'action' : 'delete',    'topic-id' : int(inode.id[1:])})
                if instruction == 'd' and parent.id[0] == 't' and inode.id[0] == 'e':
                    feedback.append({'action' : 'delete',    'topic-id' : int(parent.id[1:]), 'email-id' : str(inode.id[1:])})
        print feedback
        if not feedback:
            _info_session.destory()
            return
        ext2 = mi.apply_user_feedback( self.topic_folder.email_x_group, feedback )
        #remove log
        save_server(self)
        thread.start_new_thread(reconstruct_topic, (self.topic_folder, self.inode_map, ext2, _info_session, self.unsorted_email_folder, self))
        self.topic_folder.email_x_group = ext2
        #refresh unsorted..
        
        #reconstruct social, working...
        _remove(self.unsorted_email_folder, self.root)
        unsorted_email_folder = inode(parents = [root], children = [], type = "sub_root", name = "Unsorted Folder", id = 'ru')
        _add(unsorted_email_folder, self.root)





    def reconstruct_social(self, ext2, descriptions):
        #while self.social_folder.children:
        #   self._delete(self.social_folder.children[0], self.social_folder)
        self.social_folder.children = []
        e_x_sorted_topic = di.assign_emails(ext2, 3)
        
        
        for i in range(len(ext2[0])):
            temp_directory = inode(parents = [self.root], children = [], name =  'Social: ' + str(i) , type = "directory", id = 's' + str(i))

            #temp_directory.description = temp_directory.description + str(id) + ';'
            temp_directory.description = descriptions[i]
            self.social_folder.children.append(temp_directory)
            self.inode_map[temp_directory.id] =  temp_directory
            
            
            #Find email indice that belong in selected topic
            for j in range(len(e_x_sorted_topic)):
                if i in e_x_sorted_topic[j]:
                    try:
                        temp_directory.children.append(self.inode_map['e' + str(j)])
                        _remove(self.inode_map['e' + str(j)], self.unsorted_email_folder)
                    except:
                        x = 0
    
        self.temp_directory = [self.social_folder]
        self.load_directory

##########################################################################################
#thread for reconstruction
def reconstruct_topic(root, inode_map, ext2, _info_session, unsorted_email_folder, master):
    while root.children:
        _remove(root.children[0], root)
        
        
        
    e_x_sorted_topic = di.assign_emails(ext2, 3)
    for i in range(len(ext2[0])):
        _info_session.new_message = " New topic...(" + str(i) + " out of " + str(len(ext2[0])) + ") "
        try:
            temp_directory = inode_map['t' + str(i)]
        except:
            temp_directory = inode(parents = [root], children = [], name =  'Topic: ' + str(i) , type = "directory", id = 't' + str(i))
        
        _direct_add(temp_directory, root)
            #self.topic_folder.children.append(temp_directory)
        inode_map[temp_directory.id] =  temp_directory
        temp_directory.children = []
            
        print i
        #Find email indice that belong in selected topic
        for j in range(len(e_x_sorted_topic)):
            if i in e_x_sorted_topic[j]:
                try:
                    
                    _direct_add(inode_map['e' + str(j)], temp_directory)
                    #temp_directory.children.append(self.inode_map['e' + str(j)])
                    #_remove(inode_map['e' + str(j)], unsorted_email_folder)
                except:
                    pass


    _info_session.destory()
    save_server(master)




##########################################################################################
#Modification

def _delete(root, inode, unsorted_email_folder):
    thread.start_new_thread(_delete_thread, ( root, inode, unsorted_email_folder, ))

def _delete_thread(root, inode, unsorted_email_folder):
    _remove(inode, root)
    while len(inode.children):
        child = inode.children[0]
        _delete_thread(inode, child, unsorted_email_folder)
        
    if (not inode.parents):
        if inode.type == "email" :
            _add(inode, unsorted_email_folder)
            inode.children = []
        else:
            try:
                del self.inode_map[inode.id]
            except:
                pass

def _remove(child, parent):
    try:
        parent.children.remove(child)
    except ValueError:
        return
    try:
        child.parents.remove(parent)
    except ValueError:
        pass
        #print "d " + str(child.id) + "," + str(parent.id)
        
    _disk_writer.buffer =  _disk_writer.buffer + "d:" + str(child.id)+ '#' + str(child.code)  + ":" + str(parent.id) +  '#' + str(parent.code)+ '\n'
    _disk_writer.run()

def _direct_add(child, parent):
    parent.children.append(child)
    child.parents.append(parent)
    _disk_writer.buffer =  _disk_writer.buffer + "a:" + str(child.id)+ '#' + str(child.code)  + ":" + str(parent.id) +  '#' + str(parent.code)+ '\n'

def _add( child, parent):
    try:
        parent.children.remove(child)
    except ValueError:
        pass
    parent.children.insert(0, child)
    try:
        child.parents.remove(parent)
    except ValueError:
        pass
    child.parents.insert(0, parent)
    _disk_writer.buffer =  _disk_writer.buffer + "a:" + str(child.id)+ '#' + str(child.code)  + ":" + str(parent.id) +  '#' + str(parent.code)+ '\n'
    _disk_writer.run()

##########################################################################################
#thread for consistent load, save

def save_server(master):
    time = strftime("_%Y_%m_%d_%H_%M_%S", gmtime())
    print time
    master.log_file.close()
    temp_file_name = real_path + '/log_file/' + 'log'
    file_name = real_path + '/log_file/' + 'server_log' + time
    try:
        os.rename(temp_file_name, file_name)
    except:
        return
    ans = Dialog(master,title   = 'Saved',text = 'Successfully saved to server! File name: ' + file_name, bitmap  = 'questhead', default = 0, strings = ('Ok', 'Good'))


def save_thread(master, _info_session):
    '''Usual interface by GUI button'''

    _info_session.new_message = "Saving..."

    save_inode_tree(master.root)

    _info_session.destory()
    ans = Dialog(master,title   = 'Saved',text    = 'Successfully saved to local! File name: ' + file_name, bitmap  = 'questhead', default = 0, strings = ('Ok', 'Good!'))


def save_inode_tree(_root):
    '''Interface used by prepare script'''

    #go over inodes and write it to file.
    time = strftime("_%Y_%m_%d_%H_%M_%S", gmtime())
    print time
    queue = [_root]
    visited = set()
    count = 0
    inode_set = []
    while queue:
        temp_root = queue.pop(0)
        if temp_root not in visited:
            inode_set.append(temp_root)
            count = count + 1
            visited.add(temp_root)
            for child in temp_root.children:
                queue.append(child)

    #remove history
    all_files = glob.glob(save_file + '*')
    all_files = sorted(all_files, key=lambda x: x.lower(), reverse=True)
    
    if len(all_files) >= 2:
        for file in all_files[1:]:
            try:
                os.remove(file)
            except OSError:
                x = 0

    #new history
    temp_file_name = temp_save_file
    file_name = save_file + time
    f = open(temp_file_name, 'w')
    pickle.dump(inode_set, f)
    f.close()
    os.rename(temp_file_name, file_name)


def load_thread(_root, _info_session):
    
    
    all_files = glob.glob(save_file + '*')
    all_files = sorted(all_files, key=lambda x: x.lower(), reverse=True)
    
    
    #_info_session.new_message = "Loading Emails..."
    
    
    if all_files:
        #print "load from file: " + all_files[0]
        f = open(all_files[0])
        inode_set = pickle.load(f)
        f.close()
        _root.inode_map = {}
        for inode in inode_set:
            _root.inode_map[inode.id] = inode
        root = inode_set[0]

        _root.root = root
        _root.directory = root
        _root.temp_directory = [root]
        _root.temp_frame = []
        _root.directory_stack = [root]
        _root.topic_folder = root.children[0]
        _root.social_folder = root.children[1]
        _root.unsorted_email_folder = root.children[2]
    #root.children.append(self.unsorted_email_folder)

    #_info_session.new_message = "Training Social Model..."

    _root.social_training()
    #_info_session.destory()
    _root.loading = False


def consistent_load_thread(_root):
    all_files = glob.glob(save_file + '*')
    all_files = sorted(all_files, key=lambda x: x.lower(), reverse=True)
    if all_files:
        '''Loads most recent save file'''
        all_files = glob.glob(save_file + '*')
        all_files = sorted(all_files, key=lambda x: x.lower(), reverse=True)
        tkMessageBox.showinfo("Chekcing for consistency...", "Please wait...")
        f = open(all_files[0])
        inode_set = pickle.load(f)
        f.close()
        root = inode_set[0]
        if not consistency_check(root, _root.root):
            if not tkMessageBox.askokcancel("Load conflict!", "Override or not?..."):
                return
        
        _root.root = root
        _root.directory = root
        _root.temp_directory = [root]
        _root.temp_frame = []
        _root.directory_stack = [root]
        _root.topic_folder = root.children[0]
        _root.social_folder = root.children[1]
        _root.unsorted_email_folder = root.children[2]

    _root.load_directory()
    _root.loading = False
    tkMessageBox.showinfo("Successfully Load...", "Load from: " + all_files[0])



def create_gmail_inode_tree( mbox_filename, vocab_filename,
                             ext_filename, num_emails, 
                             txw_filename, num_topics ):
    '''
    Takes the result of the topic modeling, 
    and returns a new inode tree containing the model
    organization
    '''

    root = create_base_inode_tree()

    root = create_topic_nodes( root, num_topics, txw_filename, vocab_filename )
    
    root = populate_topic_nodes( root, mbox_filename, ext_filename, num_emails )

    return root


def create_base_inode_tree():
    '''Creates the inode structure common to all of our trees'''

    root = inode( type = "root", name = "ROOT", id = 'R')

    topic_view = inode(parents = [root], children = [],
                       type='sub root', name='Topic Folder',
                       id='rt')
    social_view = inode(parents = [root], children = [],
                       type='sub root', name='Social Folder',
                       id='rs')
    unsorted_view = inode(parents = [root], children = [],
                       type='sub root', name='Unsorted Folder',
                       id='ru')
    
    root.children = [topic_view, social_view, unsorted_view]

    return root
        

def fetch_topic_view( root ):
    '''Returns the topic view inode from an initialized tree'''
    return [child for child in root.children if child.name == "Topic Folder"][0]


def create_topic_nodes( root, num_topics, txw_filename, vocab_filename ):
    '''Adds an inode for each topic onto the passed inode tree'''
    
    topic_view = fetch_topic_view( root )

    topic_x_word = eio.load_topic_x_word( txw_filename, num_topics )

    word_lists = email_lda.print_top_n_words( topic_x_word, 
                                              vocab_filename, 
                                              constants.num_words_per_topic )

    for i in range( num_topics ): 

        topic_name =  ', '.join(map(str,word_lists[i]))

        topic_directory = inode(parents = [topic_view], 
                               children = [], 
                               name =  'Topic: ' + str(i+1), 
                               description = topic_name,
                               type = "directory", 
                               id = 't' + str(i))

        topic_view.children.append(topic_directory)

    return root


def populate_topic_nodes( root, mbox_filename, ext_filename, num_emails ):
    '''Takes a root inode with empty topic nodes, and populates them with emails'''

    topic_view = fetch_topic_view( root )
    topic_inodes = topic_view.children

    email_x_topic = eio.load_email_x_topic( ext_filename, num_emails )

    email_assignments = mi.assign_emails( email_x_topic, 
                                          constants.num_topics_per_email )

    mbox = pg.open_mbox( mbox_filename )
    mbox_ids = mbox.keys() #likely [0,n-1], but maybe not
    for i in range( num_emails ):
        print "Linking Email %d of %d" % (i+1, num_emails)

        message = eio.import_message(mbox[mbox_ids[i]])

        #Creating inode
        try:
            message['date'] = str(date_parser( message['date'] )) 
	    email_inode = inode( parents = [],
                                 name = message['sender'].strip(),
				 description = message['title'].strip(), 
                                 email_directory = [], 
                                 type = "email",
                                 children = [], 
                                 email = message, 
                                 vec = email_x_topic[i], 
                                 id = 'e' + str(i) )
	except:
            print "WARNING: exception occured in email %d" % i
            continue

        #Linking to parent topics
        for topic_id in email_assignments[i]:
            email_inode.parents.append( topic_inodes[topic_id] )
            topic_inodes[topic_id].children.append( email_inode )
    
    return root


def load_gmail_inbox_thread(_root, _thread, _info_session ):

    #building foundation inode structure
    #root inode
    root = _root.root

    topic_view = inode(parents = [root], children = children, type = "sub_root", name = "Topic Folder", id = 'rt')
    social_view = inode(parents = [root], type = "sub_root", name = "Social Folder", children = [], id = 'rs')
    unsorted_email_folder = inode(parents = [root], children = [], type = "sub_root", name = "Unsorted Folder", id = 'ru')
    
    _root.root.children = [topic_view, social_view, unsorted_email_folder]
    _root.topic_folder = topic_view
    _root.social_folder = social_view
    _root.unsorted_email_folder = unsorted_email_folder

    #not sure what this data structure accomplishes yet
    # seems like a dict containing all nodes
    _root.inode_map = {}
    _root.inode_map[root.id] = root
    _root.inode_map[topic_view.id] = topic_view
    _root.inode_map[social_view.id] = social_view
    _root.inode_map[unsorted_email_folder.id] = unsorted_email_folder
    
    #or these 
    _root.directory = root
    _root.temp_directory = []
    _root.directory_stack = [root]
    
    #load matrices and vocab from files
    topic_x_word = eio.load_topic_x_word('./model_results/gmail1_LDA_topic_x_word_30.npy', 30)
    email_x_topic = eio.load_email_x_topic('./model_results/gmail1_LDA_email_x_topic_49590.npy', 49590)
        
    #initialize sub_root node data
    topic_view.email_x_group = email_x_topic
    topic_view.group_x_individual = topic_x_word
        
    word_lists = email_lda.print_top_n_words(topic_x_word, './data/gmail1_vocab.csv', 10)
    tag_dicts = eio.load_tags('./data/gmail1_dummy_tags.csv')
    e_x_sorted_topic = di.assign_emails(email_x_topic, NUM_TOPICS_PER_EMAIL)

    
    num_topics = topic_x_word.shape[0]
    num_emails = email_x_topic.shape[0]

    #load mailbox file
    _info_session.new_message = "Openining Inbox..."
    mbox = mailbox.mbox('./data/gmail1_dummy.mbox')
    k = 0
    count = 0
    step = 1
    for i in range( num_topics ):
        
        name_name =  ', '.join(map(str,word_lists[i]))
        #print name_name
        temp_directory = inode(parents = [root], 
                               children = [], 
                               name =  'Topic: ' + str(i), 
                               description = name_name,
                               type = "directory", 
                               id = 't' + str(i))

        temp_directory.children = []
        children.append(temp_directory)
        _root.inode_map[temp_directory.id] = temp_directory
        #get emails
        cur_topic_emails = []
            
        #Find email indice that belong in selected topic
        for j in range( num_emails ):
            if i in e_x_sorted_topic[j]:
                cur_topic_emails.append(j)
        
        
        #get emails
        emails = []
        
    
        
        for mail_idx in cur_topic_emails:
            if mail_idx < 100000:
 
                
                try:
                    name_name = tag_dicts[mail_idx]['From'].strip()
                    email_directory = ''
                    tag =  tag_dicts[mail_idx]['Subject'].strip()
                    _email = pg.extract_full(mbox[mail_idx])
                    _email['date'] = str(date_parser(_email['date']))
                except:
                    _email = {'date': "0000-00-00 00:00:00", 'email': 'ah', 'title': 'ah', 'sender':'ah', 'to': 'ah'}
                    tag = 'ah'
                    name_name = 'ah'
                try:
                    email_subject = _root.inode_map['e' + str(mail_idx)]
                except:
                    email_subject = inode(parents = [], name = name_name, description = tag, email_directory = [], type = "email", children = [], email = _email, vec = email_x_topic[mail_idx], id = 'e' + str(mail_idx))
                
                
                _root.inode_map[email_subject.id] = email_subject
                email_subject.parents.append(temp_directory)
                email_subject.children = []
                emails.append(email_subject)

            k = k + 1
            if (k * 100)/(len(e_x_sorted_topic)*3) >= count:
                count = count + step
                _info_session.new_value = count
                _info_session.new_message = "Loading Gmail: " + str(i) + "-th topic (out of " + str(len(word_lists)) +  ")..." + str(count) + "%"

        temp_directory.children = emails


    _info_session.new_message = "Training Social Model..."
    _root.social_training()
    _info_session.destory()





class _load_email_(threading.Thread):
    def __init__(self, root, method, _info_session):
        threading.Thread.__init__(self, name = "load_email")
        self._run = True
        self.method = method
        self._root = root
        self._info_session = _info_session

    def run(self):
        #check_thread(self)
        if self.method == "gmail":
            load_gmail_inbox_thread(self._root, self, self._info_session)
        if self.method == "local_email":
            load_thread(self._root, self._info_session)


##########################################################################################
#check for consistency
def consistency_check(root1, root2):
    return (root1._hash() == root2._hash())
##########################################################################################
#change textfield
def change_text_field(text_field, new_text):
    text_field.config(state = 'normal')
    text_field.delete(1.0, END)
    text_field.insert(END, new_text)
    text_field.config(state = 'disabled')

################################################################################################################
#pop ups


class pop_up_log_in(Frame):
    def __init__(self,master):
        Frame.__init__(self, master)
        top=self.top=Toplevel(master)
        self.l=Label(top,text="Please Enter User Name And Password")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.ut=Label(top, text = "Username: ")
        self.ut.grid(row = 2, column = 1, sticky = EW)
        self.ut.config(state = 'disabled')
        self.u=Entry(top)
        self.u.grid(row = 2, column = 2, sticky = EW)
        self.pt=Label(top, text = "Password: ")
        self.pt.grid(row = 3, column = 1, sticky = EW)
        self.pt.config(state = 'disabled')
        self.p=Entry(top)
        self.p.grid(row = 3, column = 2, sticky = EW)
        self.b=Button(top,text='Ok',command=self.accept)
        self.b.grid(row = 4, column = 1, sticky = EW)
        self.c=Button(top,text='Cancel',command=self.cleanup)
        self.c.grid(row = 4, column = 2, sticky = EW)
        self.username = []
        self.password = []
        center(top)
    def accept(self):
        self.username = self.u.get()
        self.password = self.p.get()
        self.top.destroy()
    def cleanup(self):
        self.value=[]
        self.top.destroy()

class pop_up_insert(Frame):
    def __init__(self,master):
        Frame.__init__(self, master)
        top=self.top=Toplevel(master)
        self.l=Label(top,text="Please Enter The Name Of New Entry")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.e=Entry(top)
        self.e.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Ok',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='Cancel',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)
        self.value = []
        center(top)
    def accept(self):
        self.value=self.e.get()
        self.top.destroy()
    def cleanup(self):
        self.value=[]
        self.top.destroy()

class pop_up_delete(Frame):
    def __init__(self,master):
        Frame.__init__(self, master)
        top=self.top=Toplevel(master)
        self.l=Label(top,text="You sure to delete?")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Yes',command=self.accept)
        self.b.grid(row = 2, column = 1, sticky = EW)
        self.c=Button(top,text='No',command=self.cleanup)
        self.c.grid(row = 2, column = 2, sticky = EW)
        self.delete = False
        center(top)
    def accept(self):
        self.delete = True
        self.top.destroy()
    def cleanup(self):
        self.top.destroy()

class directory_visit:
    def __init__(self, _inode = [], _parent_inode = [], _parent_tree_node = []):
        self.inode = _inode
        self.parent_inode = _parent_inode
        self.parent_tree_node = _parent_tree_node

class pop_up_rename(Frame):
    def __init__(self,master):
        Frame.__init__(self, master)
        top=self.top=Toplevel(master)
        self.l=Label(top,text="Please Enter The New Name")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.e=Entry(top)
        self.e.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Ok',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='Cancel',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)
        self.name = []
        center(top)
    def accept(self):
        self.name = self.e.get()
        self.top.destroy()
    def cleanup(self):
        self.value=[]
        self.top.destroy()

class pop_up_add(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        top = self.top = Toplevel(master)
        self.tree = Treeview(self.top, selectmode="extended", height = 20)
        self.l=Label(top,text="Please select location to add")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.tree.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Yes',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='No',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)
        center(top)
        directory_root = directory_visit(_inode = root, _parent_tree_node = "")
        queue = [directory_root]
        visited = set()
        count = 0
        self.inode_set = []
        while queue:
            temp_root = queue.pop(0)
            #print temp_root.inode.name
            #print temp_root.parent_tree_node
            
            
            #tree.pack()
            if temp_root not in visited:
                self.inode_set.append(temp_root.inode)
                temp_id = self.tree.insert(temp_root.parent_tree_node, "end", text = temp_root.inode.name , value = count )
                count = count + 1
                visited.add(temp_root)
                for child in temp_root.inode.children:
                    directory_child = directory_visit(_inode = child, _parent_inode = temp_root.inode, _parent_tree_node = temp_id)
                    queue.append(directory_child)




class pop_up_move(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        top = self.top = Toplevel(master)
        self.tree = Treeview(self.top, selectmode="extended", height = 20)
        self.l=Label(top,text="Please select location to move")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.tree.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Yes',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='No',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)
        center(top)
        directory_root = directory_visit(_inode = root, _parent_tree_node = "")
        queue = [directory_root]
        visited = set()
        count = 0
        self.inode_set = []
        while queue:
            temp_root = queue.pop(0)
            #print temp_root.inode.name
            #print temp_root.parent_tree_node
            

            #tree.pack()
            if temp_root not in visited:
                self.inode_set.append(temp_root.inode)
                temp_id = self.tree.insert(temp_root.parent_tree_node, "end", text = temp_root.inode.name , value = count )
                count = count + 1
                visited.add(temp_root)
                for child in temp_root.inode.children:
                    directory_child = directory_visit(_inode = child, _parent_inode = temp_root.inode, _parent_tree_node = temp_id)
                    queue.append(directory_child)
    

        
        
    def accept(self):
        
        self.select = self.tree.selection()
            #
        self.select_inode = self.inode_set[self.tree.item(self.select)['values'][0]]
        if not (self.select_inode.type == "email" or self.select_inode.type == "root"):
            self.top.destroy()
    def cleanup(self):
        self.top.destroy()
################################################################################################################
class search_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master, bg = information_color)
        self.search_fix = Label(self, width = 8, bg = information_color, bd = 0, text = "Search: ", font = search_font)
        self.search_fix.pack(side = LEFT)
        self.search_text = Entry(self, width = 20, bd = 0, bg = information_color, highlightbackground = information_color, highlightcolor = information_color, font = search_font)
        
        self.search_text.pack(side = LEFT)
        self.event_handler = event_handler
        self.search_text.bind("<Return>", self.search)
    
    def search(self, event):
        self.event_handler.search(self.search_text.get())

class option_one_frame(Frame):
    def __init__(self, master, event_handler):
        pad_x = 20
        pad_y = 20
        Frame.__init__(self, master, bg = information_color, height = 30)
        
        option_1 = Label(self, text = "Insert", bd = 0, bg = information_color, font = option_one_font)
        option_1.bind("<Button-1>", event_handler.insert_entry)
        #option_1.image = insert_photo
        option_1.grid(row = 1, column = 1, padx = pad_x, pady = pad_y)
        #option_one.place(bordermode=OUTSIDE, relheight = 1, relwidth = 1)
        #delete_photo = PhotoImage(file = real_path + '/icons/delete.gif')
        option_2 = Label(self, text = "Delete", bd = 0, bg = information_color, font = option_one_font)
        option_2.bind("<Button-1>", event_handler.delete_entry)
        #option_2.image = delete_photo
        option_2.grid(row = 1, column = 2, padx = pad_x, pady = pad_y)
        option_2_5 = Label(self, text = "Rename", bd = 0, bg = information_color, font = option_one_font)
        option_2_5.bind("<Button-1>", event_handler.rename_entry)
        option_2_5.grid(row = 1, column = 3, padx = pad_x, pady = pad_y)
        
        option_3 = Label(self, text = "Move", bd = 0, bg = information_color, font = option_one_font)
        option_3.bind("<Button-1>", event_handler.move_entry)
        option_3.grid(row = 1, column = 4, padx = pad_x, pady = pad_y)
        option_3_5 = Label(self, text = "Add", bd = 0, bg = information_color, font = option_one_font)
        option_3_5.bind("<Button-1>", event_handler.add_entry)
        option_3_5.grid(row = 1, column = 5, padx = pad_x, pady = pad_y)
        option_4 = Label(self, text = "Log In", bd = 0, bg = information_color, font = option_one_font)
        option_4.bind("<Button-1>", event_handler.login_window)
        option_4.grid(row = 1, column = 6, padx = pad_x, pady = pad_y)

#option_5 = Text(self, height = 1, width = 100, state = 'disabled')
#option_5.grid(row = 1, column = 6, sticky = W)
        #option_5.config(state = 'disabled')
        
        option_7 = Label(self, text = "Save", bd = 0, bg = information_color, font = option_one_font)
        option_7.bind("<Button-1>", event_handler.save)
        option_7.grid(row = 1, column = 7, padx = pad_x, pady = pad_y)
        option_8 = Label(self, text = "Load", bd = 0, bg = information_color, font = option_one_font)
        option_8.bind("<Button-1>", event_handler.consistent_load)
        option_8.grid(row = 1, column = 8, padx = pad_x, pady = pad_y)
        #option_11 = Label(self, text = "Recons", bd = 0, bg = information_color, font = option_one_font)
        #option_11.bind("<Button-1>", event_handler.reconstruct_event)
        #option_11.grid(row = 1, column = 10, padx = pad_x, pady = pad_y)
        option_12 = Label(self, text = "Retrain", bd = 0, bg = information_color, font = option_one_font)
        option_12.bind("<Button-1>", event_handler.user_feedback_event)
        option_12.grid(row = 1, column = 11, padx = pad_x, pady = pad_y)
        option_9 = Label(self, text = "Sort", bd = 0, bg = information_color, font = option_one_font)
        option_9.bind("<Button-1>", event_handler.sort)
        option_9.grid(row = 1, column = 12, padx = pad_x, pady = pad_y)
        
        option_6 = Label(self, text = "Back", bd = 0, bg = information_color, font = option_one_font)
        option_6.bind("<Button-1>", event_handler.back)
        option_6.grid(row = 1, column = 13, padx = pad_x, pady = pad_y)

        option_10 = Label(self, text = "LoadGmail", bd = 0, bg = information_color, font = option_one_font)
        option_10.bind("<Button-1>", event_handler.load_gmail_inbox)
        option_10.grid(row = 1, column = 9, padx = pad_x, pady = pad_y)





class load_info_frame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg = information_color, height = 30)
        option_13 = Label(self, bd = 0, bg = information_color, font = option_one_font)
        option_13.grid(row = 1, column = 1, padx = 0, pady = 20, stick = E)
        self._label = option_13

class option_two_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)



class current_location_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master, bg = information_color)
        
        current_location_title = Text(self, height = 1, width = 20, insertwidth = 0, font = current_location_font, bg = information_color, highlightbackground = information_color, bd = 0)
        current_location_title.insert(END, "Current Location:")
        current_location_title.configure(state='disabled')
        current_location_title.grid(row = 1, column = 1, stick = NS)
        self.current_location = Text(self, height = 1, font = current_location_font, bg = information_color, highlightbackground = information_color, bd = 0)
        
        self.current_location.insert(END, "")
        self.current_location.configure(state='disabled')
        #current_location.
        self.current_location.grid(row = 1, column = 2, stick = NS)


class left_option_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master, bg = side_color, bd = 0)
        pad_y = 12
        pad_x = 10
        topic_view = Label(self, text = "Topic", font = left_option_font , bg = side_color, bd = 0 , pady = pad_y, padx = pad_x)
        topic_view.bind("<Button-1>", event_handler.back_to_topic)
        topic_view.grid(row = 1, column = 1, sticky = N)
        
        social_view = Label(self, text = "Social", font = left_option_font , bg = side_color, bd = 0, padx = pad_x, pady = pad_y)
        social_view.bind("<Button-1>", event_handler.back_to_social)
        social_view.grid(row = 2, column = 1, sticky = N)

        unsorted_view = Label(self, text = "Unsort", font = left_option_font , bg = side_color, bd = 0, padx = pad_x, pady = pad_y)
        unsorted_view.bind("<Button-1>", event_handler.back_to_unsorted)
        unsorted_view.grid(row = 3, column = 1, sticky = N)
#########################################################################################################
def center(win):
    """
        centers a tkinter window
        :param win: the root or Toplevel window to center
        """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()
#########################################################################################################
#directory

children_per_time = 1

class load_side_directory():
    def __init__(self, children, event_handler, _root, master):
        #threading.Thread.__init__(self, name = "load_directory")
        self.children = children
        self._run = True
        self.event_handler = event_handler
        self._root = _root
        self.name = "load_directory"
        Active_Thread.append(self)
        self.master = master
        self.info_session = info_session(master)
    
        
    def start(self):
        check_thread(self)
        self.run(0, 0)
    
    
    def run(self, i, count):

        children = self.children
        event_handler = self.event_handler
        _root = self._root
        if len(children) == 0:
            self.info_session.destory()
            return

        #i = 0
        step = 100/len(children)
        if step  == 0:
            step = 1
   
        for j in range(children_per_time):
            if not self._run or i > len(children) - 1:
                self.info_session.destory()
                return
            child = children[i]
            _root.directory.append(directory_frame(_root.canvas, child, event_handler))
            _root.canvas.create_window(0, _root._frame_height*i, anchor=NW, window=_root.directory[i])
            f = Frame(_root.canvas, width = _root._wid , height = 1, bg = separator_mid)
            _root.canvas.create_window(0, _root._frame_height*(i + 1) - 1, anchor=NW, window = f)
            i = i + 1
            if (i*100)/len(children) >= count:
                count = count + step
                self.info_session.new_value = count
                self.info_session.new_message = "loading directory..." + str(count) + "%"
        
        
        self.master.master.after(wait_time, self.run, i, count)


class top_directory_frame(Frame):
    #top = 0
    
    def __init__(self, master, event_handler, children):
        Frame.__init__(self, master)
        
        ################################################################################################

	font = tkFont.Font(family=directory_font[0], size=directory_font[1])
	(real_wid,real_height) = (font.measure("a"),font.metrics("linespace"))
        self._frame_height = real_height * 3
        self._wid = real_wid * num_directory_words
        self._height = real_height * 60
        self.canvas = Canvas(self,width = self._wid,height = self._height, scrollregion = (0, 0, self._wid * 2, (len(children))*(self._frame_height + 8)))
        self.scroll_bar = Scrollbar(self, orient=VERTICAL)
        self.scroll_bar.pack(side=RIGHT,fill=Y)
        # scroll_bar.grid(row = 1, rowspan = 800, column = 2, sticky = NS)
        self.directory = []

        self.scroll_bar.config(command = self.canvas.yview)
        #self.canvas.config(width=wid,height=800)
        self.canvas.config(yscrollcommand=self.scroll_bar.set)
        self.canvas.pack(side=LEFT,expand=True,fill=BOTH)
    
    
        ################################################################################################
        #load
        #thread.start_new_thread ( self.load, (children, event_handler ) )
        load_sd = load_side_directory(children, event_handler, self, master)
        load_sd.start()
    ################################################################################################
    
    

#progress_bar.top.destroy()



class directory_frame(Frame):
    def __init__(self, master, child, event_handler):
        Frame.__init__(self, master, highlightcolor = "grey")
        self.line_one = Text(self, height = 1, width  = num_directory_words + 2, font = directory_font)
        self.line_one.insert(END, child.name)
        self.line_one.configure(state='disabled')
        self.line_one.pack(expand = True)

        self.line_two = Text(self, height = 1, width  = num_directory_words + 2, font = description_font)
        self.line_two.insert(END,  child.description)
        self.line_two.configure(state='disabled')
        self.line_two.pack(expand = True)
        
        self.line_one.bind("<Shift-Button-1>", lambda event, select_frame = self, select_directory = child, shift_down = True: event_handler.select_directory(select_frame, select_directory, shift_down))
        self.line_two.bind("<Shift-Button-1>", lambda event, select_frame = self, select_directory = child, shift_down = True: event_handler.select_directory(select_frame, select_directory, shift_down))
        self.line_one.bind("<Button-1>", lambda event, select_frame = self, select_directory = child, shift_down = False: event_handler.select_directory(select_frame, select_directory, shift_down))
        self.line_two.bind("<Button-1>", lambda event, select_frame = self, select_directory = child, shift_down = False: event_handler.select_directory(select_frame, select_directory, shift_down))
        #self.bind("<Leave>", lambda event, select = child: self.normal_color(select))
        #self.bind("<Leave>", lambda event, select = child: self.normal_color(select))
        
        self.line_one.bind("<Double-Button-1>", lambda event, select = child: event_handler.click_directory(select))
        self.line_two.bind("<Double-Button-1>", lambda event, select = child: event_handler.click_directory(select))
    def deep_color(self):
        #
        #self.configure(bg = "grey")
        #self.temp_directory = select
        self.line_one.configure(state = 'normal')
        self.line_two.configure(state = 'normal')
        
        self.line_one.configure (bg = "grey", highlightbackground = "grey")
        self.line_two.configure (bg = "grey", highlightbackground = "grey")
        #entry.line_one.configure(state = 'disabled')
        self.line_one.configure(state = 'disabled')
        self.line_two.configure(state = 'disabled')
    
    
    def normal_color(self):
        #time.sleep(0.5)
        #self.temp_directory = select
        self.line_one.configure(state = 'normal')
        self.line_two.configure(state = 'normal')
        
        self.line_one.configure (bg = "white", highlightbackground = "white")
        self.line_two.configure (bg = "white", highlightbackground = "white")
        self.line_one.configure(state = 'disabled')
        self.line_two.configure(state = 'disabled')
    def callback(self, event):
        print "clicked at", event.x, event.y


#########################################################################################################
#info session
class info_session():
    def __init__(self, master):
	font = tkFont.Font(family=directory_font[0], size=directory_font[1])
	(real_wid,real_height) = (font.measure("a"),font.metrics("linespace"))
        self.master = master
        self.pb_hD = ttk.Progressbar(master, orient='horizontal', mode='determinate', length = real_wid*40)
        self.pb_hD.grid(row = 4, column = 1, columnspan = all_column, sticky = EW)
        self.info = load_info_frame(master)
        self.info.grid(row = 1, column = 7, sticky = EW)
        self.master = master
        self.old_value = 0
        self.new_value = 0
        self.old_message = ''
        self.new_message = ''
        self._run = True
        self.count = 0
        self.update()

    
    def update(self):
        self.count = self.count + 1
        if self.count > 100000/wait_time:
            return
        if not self._run:
            return
        if self.new_value > self.old_value:
            self.pb_hD.step(self.new_value - self.old_value)
            self.old_value = self.new_value
        if not self.new_message == self.old_message:
            self.info._label.configure(text = self.new_message)
            self.old_message = self.new_message
        self.master.master.after(wait_time, self.update)

    def destory(self):
        self.pb_hD.grid_forget()
        self.info.grid_forget()
        self._run = False



#########################################################################################################
#email
class email_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        
        top_section = Frame(self);
        top_section.grid(row = 1, column = 1, sticky = EW)

        self.date = Text(top_section, height = 1, width = 50, font = title_date_font)
        self.date.grid(row = 1, column = 2, sticky = NE)
        self.date.insert(END, "xx-xx-xxxx")
        
     
        
        
        information_section = Frame(top_section)
        information_section.grid(row = 1, column = 1, sticky = EW)
        
        sender_section = Frame(information_section)
        sender_section.grid(row = 1, column = 1, sticky = EW)
        sender_fix = Text(sender_section, height = 1,  width = 9, font = email_title_font)
        sender_fix.grid(row = 1, column = 1, sticky = NW)
        sender_fix.insert(END, "Sender: ")
        sender_fix.configure(state = 'disable')
        self.sender = Text(sender_section, height = 1, width = 50, font = title_info_font)
        self.sender.grid(row = 1, column = 2, sticky = NW)
        self.sender.insert(END, " ")
        self.sender.configure(state = 'disable')
        
        to_section = Frame(information_section)
        to_section.grid(row = 2, column = 1, sticky = EW)
        to_fix = Text(to_section, height = 1, width = 9, font = email_title_font)
        to_fix.grid(row = 1, column = 1, sticky = NW)
        to_fix.insert(END, "To: ")
        to_fix.configure(state = 'disable')
        self.to = Text(to_section, height = 1,  width = 50, font = title_info_font)
        self.to.grid(row = 1, column = 2, sticky = NW)
        self.to.insert(END, " ")
        self.to.configure(state = 'disable')
        
        title_section = Frame(information_section)
        title_section.grid(row = 3, column = 1, sticky = EW)
        title_fix = Text(title_section, width = 7, height = 1, font = email_title_font)
        title_fix.grid(row = 1, column = 1, sticky = NW)
        title_fix.insert(END, "Title: ")
        title_fix.configure(state = 'disable')
        self.title = Text(title_section, height = 1,  width = 50, font = title_text_font)
        self.title.grid(row = 1, column = 2, sticky = NW)
        self.title.insert(END, " ")
        self.title.configure(state = 'disable')
        
        f = Frame(self, height = separator_huge_height, bg = separator_dark)
        f.grid(row = 2, column = 1, columnspan = 2, sticky = EW)

        self.email_text = Text(self, height = 30, width = 150, font = email_font)
        self.email_text.grid(row = 3, column = 1, sticky = EW)
        self.email_text.configure(state = 'disable')
        
        f = Frame(self, height = separator_huge_height, bg = separator_dark)
        f.grid(row = 4, column = 1, columnspan = 2, sticky = EW)

        keywords_fix = Text(self, height = 1,  width = 9,  font = email_title_font)
        keywords_fix.grid(row = 5, column = 1, sticky = W)
        keywords_fix.insert(END, "Keywords: ")
        keywords_fix.configure(state = 'disable')
        self.keywords = Text(self,   font = title_info_font, height = 10)
        self.keywords.grid(row = 6, column = 1, sticky = W)
        self.keywords.insert(END, " ")
        self.keywords.configure(state = 'disable')


#########################################################################################################
#check thread
def check_thread(id):
    
    for key in Active_Thread:
        try:
            if key.name == id.name and not key == id:
                print key, id

                key._run = False
                Active_Thread.remove(key)
        except:
            pass

#########################################################################################################
#key words
class keywords_frame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        keywords_fix = Text(self, height = 1,  width = 9)
        keywords_fix.grid(row = 1, column = 1, sticky = W)
        keywords_fix.insert(END, "Keywords: ")
        keywords_fix.configure(state = 'disable')
        self.keywords = Text(self, height = 1)
        self.keywords.grid(row = 1, column = 2, sticky = W)
        self.keywords.insert(END, " ")
        self.keywords.configure(state = 'disable')


def load_email_thread(tf, root, children):
    tf.loading = True
    topic_x_word = eio.load_topic_x_word('./model_results/round3_LDA_topic_x_word_30.npy', 30)
    word_lists = email_lda.print_top_n_words(topic_x_word, './data/round3_vocab.csv', 10)
    ext = eio.load_email_x_topic('./model_results/round3_LDA_email_x_topic_FULL_14453.npy', 14453)
    tf.topic_folder.ext = ext
    tag_dicts = eio.load_tags('./data/round3_full_tags.csv')
    e_x_sorted_topic = di.assign_emails(ext, 3)
    for i in range(len(word_lists)):
        name_name =  ', '.join(map(str,word_lists[i]))
        #print name_name
        temp_directory = inode(parents = [root], children = [], name =  'Topic: ' + str(i), description = name_name, type = "directory", id = 't' + str(i))
        
        children.append(temp_directory)
        tf.inode_map[temp_directory.id] =  temp_directory
        #get emails
        cur_topic_emails = []
        
        #Find email indice that belong in selected topic
        for j in range(len(e_x_sorted_topic)):
            if i in e_x_sorted_topic[j]:
                cur_topic_emails.append(j)
    
        #get emails
        emails = []
        for mail_idx in cur_topic_emails:
            if mail_idx < 100000:
                name_name = tag_dicts[mail_idx]['From'].strip()
                email_directory = './sarahs_inbox/parsed/msnbc/txt/' + tag_dicts[mail_idx]['filename'].strip().replace(";", "")
                tag =  tag_dicts[mail_idx]['Subject'].strip()
                _email = tf.read_email_text(email_directory)
                email_subject = inode(parents = [temp_directory], name = name_name, description = tag, email_directory = email_directory, type = "email", children = [], email = _email, vec = ext[mail_idx], id = 'e' + str(mail_idx))
                #print email_subject.vec
                tf.inode_map[email_subject.id] =  email_subject
                emails.append(email_subject)
        temp_directory.children = emails
    children.append(temp_directory)
#tf.social_training()
    tf.loading = False

root=None #making us able to refer to it outside the module
def main():

    tk = Tk()

    #eh = event_handler(tk)
    root = inode( type = "root", name = "ROOT", id = 'R')
    children = []
    topic_view = inode(parents = [root], children = children, type = "sub_root", name = "Topic Folder", id = 'rt')
    social_view = inode(parents = [root], type = "sub_root", name = "Social Folder", children = [], id = 'rs')
    unsorted_email_folder = inode(parents = [root], children = [], type = "sub_root", name = "Unsorted Folder", id = 'ru')
    root.children = [topic_view, social_view, unsorted_email_folder] 

    tf = test_frame(tk, root)
    tf.inode_map[root.id] = root
    tf.inode_map[topic_view.id] = topic_view
    tf.inode_map[social_view.id] = social_view
    tf.inode_map[unsorted_email_folder.id] = unsorted_email_folder
    
    tf.pack()
    s = Style()
    s.theme_use("default")
    s.configure("TProgressbar", thickness=1, foreground= information_color, background= 'red', border = 0, padding = 0)
    #thread.start_new_thread ( tf.load, ())
    #tf.consistent_load()
    #satf.search('s')
    #thread.start_new_thread(load_email_thread, (tf, topic_view, children))
    tk.mainloop()

    tk.quit()

if __name__ == '__main__':
    main()


