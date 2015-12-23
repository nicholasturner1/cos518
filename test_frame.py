import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
import parse_emails as pe
import gensim
import time
import numpy as np
import argparse
import disp_interface as di
import scipy as sp
from scipy import io
from ttk import *
from Tkinter import *
import email as em
import imaplib

import email_lda

TYPE = ["root", "email", "directory", "unknown", "unsorted_email_folder"]

class inode:
    def __init__(self, parents = [], children = [], name = "New Entry", description = "" , type = "unknown", email_directory = "", email = []):
        self.parents = parents
        self.children = children
        self.name = name
        self.type = type
        self.description = description
        self.email_directory = email_directory
        self.email = email

class test_frame(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        
        event_handler = self
        
        option_one = option_one_frame(self, event_handler)
        #option_one.pack()
        #option_one.place(height = 200, width = 500)
        option_one.grid(row = 1, column = 1, columnspan = 8, sticky = W)
        
        
        option_two = option_two_frame(self, event_handler)
        option_two.grid(row = 2, column = 1, columnspan = 8)
        
        
        current_location = current_location_frame(self, event_handler)
        current_location.grid(row = 3, column = 1, columnspan = 8, sticky = W)
        self.current_location = current_location.current_location;
        
        f = Frame(self, height = 1, bg = "black")
        f.grid(row = 4, column = 1, columnspan = 8, sticky = EW)
        
        left_option = left_option_frame(self, event_handler)
        left_option.grid(row = 5, column = 1, sticky = NW)
        
        
        
        self.top_directory = top_directory_frame(self, event_handler, root.children)
        #top_directory = Frame(self, width=100, height=100)
        #top_directory.bind("<Button-1>", self.callback)
        self.top_directory.grid(row = 5, column = 3, sticky = NW)
        #self.directories = top_directory.directory
        
        f = Frame(self, width = 1, bg = "black")
        f.grid(row = 5, column = 4, sticky = NS)
        
        f = Frame(self, width = 1, bg = "black")
        f.grid(row = 5, column = 2, sticky = NS)
        
        email_f = email_frame(self, event_handler)
        email_f.grid(row = 5, column = 5, columnspan = 4, sticky = N)
        self.email = email_f
    
    
    
        self.root = root
        self.directory = root
        self.temp_directory = root
        self.temp_frame = []
        self.directory_stack = [root]
        self.topic_folder = root.children[0]
        self.social_folder = root.children[1]
        self.unsorted_email_folder = root.children[2]
        #root.children.append(self.unsorted_email_folder)
        self.load_directory()
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
    def select_directory(self, select_frame, select_directory):
        
        if self.temp_frame:
            self.temp_frame.normal_color()
        
        self.temp_frame = select_frame
        self.temp_frame.deep_color()
        self.temp_directory = select_directory
            #print self.temp_directory.type
    

    def click_directory(self, select):
    
        if select.type == "email":
            self.load_email(select)
        else:
            #print self.directory.name
            
            self.directory = select
            self.directory_stack.append(self.directory)
            self.load_directory()
            self.current_location.configure(state='normal')
            self.current_location.delete(1.0, END)
            self.current_location.insert(END, select.description)
            self.current_location.configure(state='disabled')
            self.change_current_location()
    ##########################################################################################


    def load_email(self, inode):
        self.email.sender.configure(state = 'normal')
        #self.email.sender.delete(1.0, END)
        #self.email.sender.insert(END, "ggbba")
        self.email.sender.configure(state = 'disabled')
        #print inode.email_directory
        _email = inode.email
        if not _email:
            _email = self.read_email_text(inode.email_directory)
        #print email_text
        self.email.email_text.configure(state = 'normal')
        self.email.email_text.delete(1.0, END)
        self.email.email_text.insert(INSERT, _email[0])
        self.email.email_text.configure(state = 'disabled')
        
        self.email.sender.configure(state = 'normal')
        self.email.sender.delete(0.0, END)
        self.email.sender.insert(INSERT, _email[1])
        self.email.sender.configure(state = 'disabled')
        
        self.email.to.configure(state = 'normal')
        self.email.to.delete(0.0, END)
        self.email.to.insert(INSERT, _email[2])
        self.email.to.configure(state = 'disabled')
        
        self.email.title.configure(state = 'normal')
        self.email.title.delete(0.0, END)
        self.email.title.insert(INSERT, _email[3])
        self.email.title.configure(state = 'disabled')
        
        self.email.date.configure(state = 'normal')
        self.email.date.delete(0.0, END)
        self.email.date.insert(INSERT, _email[4])
        self.email.date.configure(state = 'disabled')
    
    
    def load_directory(self):
        children = self.directory.children
        children = self.sort_children(children)
        #print children
        self.top_directory.forget()
        self.top_directory = top_directory_frame(self, self, children)
        self.top_directory.grid(row = 5, column = 3, sticky = NW)

    def sort_children(self, children):
        if children[0].type != "email":
            return children
        
        #load the email contents for sorting purposes
        for child in children:
            child.email = self.read_email_text(child.email_directory)
        
        dropdown = 1 
        #sort emails based on dropdown
        if dropdown == 0: #sort by sender
            sorted_children = sorted(children, key=lambda x: x.email[1].lower(), reverse=False)
        elif dropdown == 1: #sort by subject
            sorted_children = sorted(children, key=lambda x: x.email[3].lower(), reverse=False)
        else:
            sorted_children = children

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

    def back_to_unsorted(self):
        new_directory  = self.unsorted_email_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = new_directory
        self.change_current_location()
        self.load_directory()

    def back_to_social(self):
        new_directory  = self.social_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = new_directory
        self.change_current_location()
        self.load_directory()
        
    def back_to_topic(self):
        new_directory  = self.topic_folder
        self.directory_stack = [self.root, new_directory]
        self.directory = new_directory
        self.temp_directory = new_directory
        self.change_current_location()
        self.load_directory()



    def read_email_text(self, filename):
        with open(filename) as f:
            #print f
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
        return [_email, sender, to, title, date]
    ##########################################################################################
    #insertion and deletion
    
    def insert_entry(self):
        self._pop_up_insert = pop_up_insert(self.master)
        self.master.wait_window(self._pop_up_insert.top)
        if self._pop_up_insert.value:
            
            self.directory.children.insert(0, inode(name = self._pop_up_insert.value, parents = [self.directory], children = []))
            #self.temp_directory.name = self._pop_up_insert.value;
            self.load_directory()
        
    def delete_entry(self):
        if self.temp_directory.type == "unsorted_email_folder":
            return
        self._pop_up_delete = pop_up_delete(self.master)
        self.master.wait_window(self._pop_up_delete.top)
        
        if self._pop_up_delete.delete:
            for child in self.temp_directory.children:
                self._remove(child, self.temp_directory)
                if child.type == "email" and (not child.parents):
                    self._add(child, self.unsorted_email_folder)
        
            for parent in self.temp_directory.parents:
                self._remove(self.temp_directory, parent)


            #check if email
            
            #print self.temp_directory.parents
            if self.temp_directory.type == "email" and (not self.temp_directory.parents):
             
                self._add(self.temp_directory, self.unsorted_email_folder)
                self.temp_directory.children = []

            self.load_directory()
    ##########################################################################################
    #add and move entry
    def move_entry(self):
        if not self.temp_directory.type == "email":
            return
        
        self._pop_up_move = pop_up_move(self.master, self.root)
        self.wait_window(self._pop_up_move.top)
        if self._pop_up_move.select_inode:
        #print "here"
            parent = self.directory
            child = self.temp_directory
            child.children = []
        #self.directory.children.remove(child)
            self._remove(child, parent)
            self._add(child, self._pop_up_move.select_inode)
            
            self.load_directory()
    def add_entry(self):
        if not self.temp_directory.type == "email":
            return
        
        self._pop_up_move = pop_up_move(self.master, self.root)
        self.wait_window(self._pop_up_move.top)
        if self._pop_up_move.select_inode:
            #print "here"
            parent = self.directory
            child = self.temp_directory
            child.children = []
            #self.directory.children.remove(child)
            #self._remove(child, parent)
            self._add(child, self._pop_up_move.select_inode)
            
            self.load_directory()
    ##########################################################################################
    #add and remove inode
    def _remove(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            x = 0
        try:
            child.parents.remove(parent)
        except ValueError:
            x = 0
    def _add(self, child, parent):
        try:
            parent.children.remove(child)
        except ValueError:
            x = 0
        parent.children.append(child)
        try:
            child.parents.remove(parent)
        except ValueError:
            x = 0
        child.parents.append(parent)

    ##########################################################################################
    #log in, load new emails
    def login_window(self):
        self._pop_up_log_in = pop_up_log_in(self.master)
        self.master.wait_window(self._pop_up_log_in.top)
        if self._pop_up_log_in.username:
            self.login(self._pop_up_log_in.username, self._pop_up_log_in.password)
    
    def login(self, username, password):
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

            child = inode(parents = [self.unsorted_email_folder], name = sender[0], description = title, email = [body, sender, to, title, date], children = [], type = "email")
            self.unsorted_email_folder.children.append(child)



    def parse_email_remote(self, raw_email):
        email_message = em.message_from_string(raw_email)
        to =  email_message['To']
        sender = em.utils.parseaddr(email_message['From']) # for parsing "Yuji Tomita" <yuji@grovemade.com>
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
# not multipart - i.e. plain text, no attachments, keeping fingers crossed
        else:
            body = b.get_payload(decode=True)


        email = body
        return [sender, to, title, date, body]


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

class pop_up_add(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        top = self.top = Toplevel(master)
        self.tree = Treeview(self.top, selectmode="extended", height = 20)
        
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

        self.l=Label(top,text="Please select location to add")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.tree.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Yes',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='No',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)

class pop_up_move(Frame):
    def __init__(self, master, root):
        Frame.__init__(self, master)
        top = self.top = Toplevel(master)
        self.tree = Treeview(self.top, selectmode="extended", height = 20)

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
    
        self.l=Label(top,text="Please select location to move")
        self.l.grid(row = 1, column = 1, columnspan = 2, sticky = EW)
        self.tree.grid(row = 2, column = 1, columnspan = 2, sticky = EW)
        self.b=Button(top,text='Yes',command=self.accept)
        self.b.grid(row = 3, column = 1, sticky = EW)
        self.c=Button(top,text='No',command=self.cleanup)
        self.c.grid(row = 3, column = 2, sticky = EW)
        
    def accept(self):
        
        self.select = self.tree.selection()
            #
        self.select_inode = self.inode_set[self.tree.item(self.select)['values'][0]]
        if not (self.select_inode.type == "email" or self.select_inode.type == "root"):
            self.top.destroy()
    def cleanup(self):
        self.top.destroy()
################################################################################################################

class option_one_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        option_1 = Button(self, text = "Insert", command = event_handler.insert_entry)
        option_1.grid(row = 1, column = 1, sticky = W)
        #option_one.place(bordermode=OUTSIDE, relheight = 1, relwidth = 1)
        option_2 = Button(self, text = "Delete", command = event_handler.delete_entry)
        option_2.grid(row = 1, column = 2, sticky = W)
        
        option_3 = Button(self, text = "Move", command = event_handler.move_entry)
        option_3.grid(row = 1, column = 3, sticky = W)
        option_3 = Button(self, text = "Add", command = event_handler.add_entry)
        option_3.grid(row = 1, column = 4, sticky = W)
        option_4 = Button(self, text = "Log In", command = event_handler.login_window)
        option_4.grid(row = 1, column = 5, sticky = E)
#option_one.pack()
#option_one.place(bordermode=OUTSIDE, height = 100, width = 100)
        #option_two = Button(self, text = "Delete")
        #option_two.pack()
        #option_two.place(height = 200, width = 500, relx = 0, rely = 0.3)



class option_two_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        option_one = Button(self, text = "back")
        option_one.bind("<Button-1>", event_handler.back)
        option_one.pack()


class current_location_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        current_location_title = Text(self, height = 1, width = 20)
        current_location_title.insert(END, "Current Location:")
        current_location_title.configure(state='disabled')
        current_location_title.grid(row = 1, column = 1)
        self.current_location = Text(self, height = 1)
        
        self.current_location.insert(END, "")
        self.current_location.configure(state='disabled')
        #current_location.
        self.current_location.grid(row = 1, column = 2)


class left_option_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        topic_view = Button(self, text = "Topic View", command = event_handler.back_to_topic)
        topic_view.grid(row = 1, column = 1, sticky = N)
        
        social_view = Button(self, text = "Social View", command = event_handler.back_to_social)
        social_view.grid(row = 2, column = 1, sticky = N)

        unsorted_view = Button(self, text = "Unsorted", command = event_handler.back_to_unsorted)
        unsorted_view.grid(row = 3, column = 1, sticky = N)

class top_directory_frame(Frame):
    #top = 0
    
    def __init__(self, master, event_handler, children):
        Frame.__init__(self, master)
        #print children
        #self.bind("<Enter>", self.callback)
        wid = 200
        self.canvas = Canvas(self,width=wid,height=1000, scrollregion=(0, 0, 10000, 10000))
        self.scroll_bar = Scrollbar(self, orient=VERTICAL)
        self.scroll_bar.pack(side=RIGHT,fill=Y)
        # scroll_bar.grid(row = 1, rowspan = 800, column = 2, sticky = NS)
        self.directory = []
        i = 0
        for child in children:
            self.directory.append(directory_frame(self.canvas, child, event_handler))
                        #self.directory[i].grid(row = (2*i + 1), column = 1, sticky = NW)
            self.canvas.create_window(0, 45*i, anchor=NW, window=self.directory[i])
            #self.directory[i].pack(side = TOP)
            self.f = Frame(self.canvas, width = wid, height = 1, bg = "black")
            self.canvas.create_window(0, 45*i, anchor=NW, window=self.f)
            i = i + 1
        

        self.scroll_bar.config(command = self.canvas.yview)
        self.canvas.config(width=wid,height=1000)
        self.canvas.config(yscrollcommand=self.scroll_bar.set)
        self.canvas.pack(side=LEFT,expand=True,fill=BOTH)
    


#self.directory.insert

class directory_frame(Frame):
    def __init__(self, master, child, event_handler):
        Frame.__init__(self, master, highlightcolor = "grey")
        self.line_one = Text(self, height = 1, width  = 30)
        self.line_one.insert(END, child.name)
        self.line_one.configure(state='disabled')
        self.line_one.pack(expand = True)

        self.line_two = Text(self, height = 1, width  = 30)
        self.line_two.insert(END,  child.description)
        self.line_two.configure(state='disabled')
        self.line_two.pack(expand = True)
        self.line_one.bind("<Button-1>", lambda event, select_frame = self, select_directory = child: event_handler.select_directory(select_frame, select_directory))
        self.line_two.bind("<Button-1>", lambda event, select_frame = self, select_directory = child: event_handler.select_directory(select_frame, select_directory))
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

class email_frame(Frame):
    def __init__(self, master, event_handler):
        Frame.__init__(self, master)
        
        
        top_section = Frame(self);
        top_section.grid(row = 1, column = 1, sticky = EW)

        self.date = Text(top_section, height = 1, width = 50)
        self.date.grid(row = 1, column = 2, sticky = NE)
        self.date.insert(END, "xx-xx-xxxx")
        
        
        information_section = Frame(top_section)
        information_section.grid(row = 1, column = 1, sticky = EW)
        
        sender_section = Frame(information_section)
        sender_section.grid(row = 1, column = 1, sticky = EW)
        sender_fix = Text(sender_section, height = 1,  width = 9)
        sender_fix.grid(row = 1, column = 1, sticky = W)
        sender_fix.insert(END, "Sender: ")
        sender_fix.configure(state = 'disable')
        self.sender = Text(sender_section, height = 1)
        self.sender.grid(row = 1, column = 2, sticky = W)
        self.sender.insert(END, " ")
        self.sender.configure(state = 'disable')
        
        to_section = Frame(information_section)
        to_section.grid(row = 2, column = 1, sticky = EW)
        to_fix = Text(to_section, height = 1, width = 5)
        to_fix.grid(row = 1, column = 1, sticky = W)
        to_fix.insert(END, "To: ")
        to_fix.configure(state = 'disable')
        self.to = Text(to_section, height = 1)
        self.to.grid(row = 1, column = 2, sticky = W)
        self.to.insert(END, " ")
        self.to.configure(state = 'disable')
        
        title_section = Frame(information_section)
        title_section.grid(row = 3, column = 1, sticky = EW)
        title_fix = Text(title_section, width = 7, height = 1)
        title_fix.grid(row = 1, column = 1, sticky = W)
        title_fix.insert(END, "Title: ")
        title_fix.configure(state = 'disable')
        self.title = Text(title_section, height = 1)
        self.title.grid(row = 1, column = 2, sticky = W)
        self.title.insert(END, " ")
        self.title.configure(state = 'disable')
        
        f = Frame(self, height = 1, bg = "black")
        f.grid(row = 2, column = 1, columnspan = 1, sticky = EW)

        self.email_text = Text(self, height = 40)
        self.email_text.grid(row = 3, column = 1, sticky = EW)
        self.email_text.configure(state = 'disable')

#class event_handler:
#   def __init__(self, fields):
#       self.fields = fields
#
#   def insert_entry(self):
#       self.fields.current_location.insert(END, "GOOD")



if __name__ == '__main__':
    tk = Tk()
    #eh = event_handler(tk)
    root = inode( type = "root", name = "ROOT")
    children = []
    topic_view = inode(parents = [root], children = children, type = "directory", name = "Topic Folder")
    social_view = inode(parents = [root], type = "diectory", name = "Social Folder")
    unsorted_email_folder = inode(parents = [root], children = [], type = "unsorted_email_folder", name = "Unsorted Folder")
    root.children = [topic_view, social_view, unsorted_email_folder]


    topic_x_word = pe.load_topic_x_word('./model_results/round3_LDA_topic_x_word_30.npy', 30)
    word_lists = email_lda.print_top_n_words(topic_x_word, './data/round3_vocab.csv', 10)
    ext = pe.load_email_x_topic('./model_results/round3_LDA_email_x_topic_FULL_14453.npy', 14453)
    tag_dicts = pe.load_tags('./data/round3_full_tags.csv')
    e_x_sorted_topic = di.assign_emails(ext, 3)
    for i in range(len(word_lists)):
        name_name =  ', '.join(map(str,word_lists[i]))
        #print name_name
        temp_directory = inode(parents = [topic_view], name =  'Topic: ' + str(i), description = name_name, type = "directory")
        children.append(temp_directory)
        
        #get emails
        cur_topic_emails = []
        
        #Find email indice that belong in selected topic
        for j in range(len(e_x_sorted_topic)):
            if i in e_x_sorted_topic[j]:
                cur_topic_emails.append(j)
    
        #get emails
        emails = []
        for mail_idx in cur_topic_emails:
            if mail_idx < 100:
                name_name = tag_dicts[mail_idx]['filename']
                email_directory = './sarahs_inbox/parsed/msnbc/txt/' + name_name
                tag =  tag_dicts[mail_idx]['From'].strip() + ' -- ' + tag_dicts[mail_idx]['Subject'].strip()
                email_subject = inode(parents = [temp_directory], name = name_name, description = tag, email_directory = email_directory, type = "email")
                emails.append(email_subject)

        temp_directory.children = emails

    

    tf = test_frame(tk, root)
#tf.login('setsee0000@gmail.com', 'B-Dap3ub')
    tf.pack()
    tk.mainloop()
