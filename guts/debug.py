'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from datetime import datetime
import sys
from traceback import print_stack


class Debug(object):
    
    def __init__(self):
        self.logfile = open("debug.txt","a+")
        self.logfile.write("Execution started " +repr(datetime.now()) + "\n")
        self.fog = True
        self.info = False
        self.test = False
        self.active = False

    def log(self, msg):
        logstring = "Debug logging: " + msg + "\n"
        sys.stderr.write(logstring)
        self.logfile.write(logstring)
        print_stack(file = self.logfile)
        
    def activate(self):
        self.active = True
        #self.fog = False
        self.test = True    
        self.info = True
        
debug = Debug()
