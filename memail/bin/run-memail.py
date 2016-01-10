#!/usr/bin/env python

from memail import frame

#This is obviously minimal, and seems silly,
# but in order to load (unpickle) the inode tree
# saved in prepare_memail properly, we need to call
# frame as memail.frame within another module. Luckily,
# this script does just that
frame.main()
