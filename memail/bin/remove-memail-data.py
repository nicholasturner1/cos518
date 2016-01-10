#!/usr/bin/env python

from memail import constants
import os, glob

user_data_dir = os.path.dirname( constants.output_prefix )

data_files = glob.glob( user_data_dir + "/*" )

for f in data_files:
    os.remove(f)


