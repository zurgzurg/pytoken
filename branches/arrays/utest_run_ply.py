#!/usr/bin/env python
import os
import time
import sys
import subprocess

def get_list_of_tests():
    tlist = []
    for f in os.listdir("."):
        if f.startswith("utest_ply") and f.endswith(".py"):
            tlist.append(f)
    return tlist

def run_one_test(tname):
    obj = subprocess.Popen(["python", tname])
    while obj.returncode is None:
        time.sleep(0.1)
        obj.poll()
    if obj.returncode != 0:
        print "Failed ", tname
    else:
        print "Pass   ", tname
    return

def run_tests(tlist):
    for tname in tlist:
        run_one_test(tname)
    return

tlist = get_list_of_tests()
run_tests(tlist)

sys.exit(0)
