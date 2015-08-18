# main.py - Entry-point for `list-tree'
# author: Ben Simner 
'''Implements list-tree

Attempts to imitate ls in operation and arguments, but instead displays as a tree-view
'''

import os
import time
import math
from docopt import docopt
from collections import namedtuple

def main():
    doc = """
    Usage:
        lt [--color=<when>] [--max-depth=<depth>] [-aABhl] [<dir>]

    Options: 
    <dir>                   Directory to read from 
    --color=<when>          Colorize the output, can be 'never', 'auto' or 'always' [default: always]
    --max-depth=<depth>     Maximum depth to branch to [default: 3]
    -a --all                Do not ignore entries starting with .
    -A --almost-all         Like -a except do not list implied . and ..
    -B --ignore-backups     Do not list entries ending with ~
    -h --human-readable     With -l, print human-readable sizes
    -l                      Use long-list format
"""
    args = docopt(doc) 
    _main(**args)

def _main(**argv):
    cwd = os.getcwd()

    global MAX_DEPTH
    global COLOR_MODE
    global LIST_ALL 
    global IGNORE_BACKUPS
    global LONG_LIST
    global HUMAN_READABLE

    MAX_DEPTH = int(argv['--max-depth'])
    COLOR_MODE = argv['--color']

    if argv['--all']:
        LIST_ALL = 2
    elif argv['--almost-all']:
        LIST_ALL = 1
    else:
        LIST_ALL = 0

    if argv['<dir>']:
        cwd = argv['<dir>']

    IGNORE_BACKUPS = argv.get('--ignore-backups', False)
    HUMAN_READABLE = argv.get('--human-readable', False)
    LONG_LIST = argv.get('-l', False)

    lines = print_tree(os.path.realpath(cwd))
    
    if LONG_LIST:
        print_long_list_fmt(lines)
    else:
        for struct in lines:
            print(struct.pretty_str)

def print_long_list_fmt(lines):
    # generate prefixes
    prefix_strs = []
    max_lens = [0,0,0]
    for struct in lines:
        if struct.path:
            prefixs = []
            attrs = get_attributes(struct.path)

            prefix = '' 
            prefix += 'd' if attrs.isdir else '-'
            prefix += 'x' if attrs.executable else '-'
            prefix += 'r' if attrs.readable else '-'
            prefix += 'w' if attrs.writeable else '-'
            prefixs.append(prefix)
            if len(prefix) > max_lens[0]:
                max_lens[0] = len(prefix)

            prefix = '' 
            if not HUMAN_READABLE:
                prefix += str(attrs.size) + 'B'
            else:
                if attrs.size <= 0:
                    prefix += '0B'
                else: 
                    log = round(math.log(attrs.size, 10))
                    if log < 3: 
                        prefix += str(attrs.size) + 'B'
                    elif log < 6:
                        prefix += '%.3f' % (attrs.size / 1024) + 'KB'
                    elif log < 9:
                        prefix += '%.3f' % (attrs.size / (1024 ** 2)) + 'MB'
                    else:
                        prefix += '%.3f' % (attrs.size / (1024 ** 3)) + 'GB'

            prefixs.append(prefix)
            if len(prefix) > max_lens[0]:
                max_lens[1] = len(prefix)
            
            prefix = '' 
            prefix += time.strftime('%b %d %Y %H:%M', time.gmtime(attrs.last_modified))
            prefixs.append(prefix)
            if len(prefix) > max_lens[2]:
                max_lens[2] = len(prefix)

            prefix_strs.append(prefixs)
        else:
            prefix_strs.append(['', '', ''])

    for prefixs, struct in zip(prefix_strs, lines):
        prefix = ''
        for p, max_len in zip(prefixs, max_lens):
            prefix += p + ' '*(3 + max_len - len(p))
        print(prefix + struct.pretty_str)

class bcolors:
    '''ANSI escape sequences'''
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

Attributes = namedtuple('FileAttributes', ['size', 'isdir', 'executable', 'readable', 'writeable', 'last_modified'])

def get_attributes(path):
    return Attributes(
        os.path.getsize(path), 
        os.path.isdir(path),
        os.access(path, os.X_OK),
        os.access(path, os.R_OK),
        os.access(path, os.W_OK),
        os.path.getmtime(path)
    )

def get_print_string_file(path, indent=''):
    '''returns the printstring for some file with realpath 'path'
    includes ANSI color tags 
    given some indent
    '''
    s = indent + '|-- '
    f = os.path.basename(path)

    col = ''
    x = ''

    attr = get_attributes(path)

    if attr.executable:
        col = bcolors.BOLD + bcolors.OKGREEN
        x += '*'

    if COLOR_MODE == 'always' or COLOR_MODE == 'auto':
        s += col + f + bcolors.ENDC + bcolors.BOLD + x + bcolors.ENDC
    else:
        s += f + x

    return s

def get_print_string_dir(path, indent=''):
    '''returns the printstring for some dir with realpath 'path'
    includes ANSI color tags 
    given some indent
    '''
    s = indent
    d = os.path.basename(path)

    attr = get_attributes(path)

    col = bcolors.BOLD + bcolors.OKBLUE

    if COLOR_MODE == 'always' or COLOR_MODE == 'auto':
        s += col + d + bcolors.ENDC + '/'
    else:
        s += d + '/'

    return s

PrettyStruct = namedtuple('File', ['pretty_str', 'path'])

def print_tree(wd, level=0):
    '''Returns pretty-prints tree structure starting at 'wd' i.e.:
        wd/
        |--- file1
        |--- file2
        |--- dir/
            |---- ...
        |--- .../

    on each dir the level increases by 1
    '''
    lines = []

    pre_indent = ' '*2*level
    post_indent = ' '*2*(level + 1)
    
    s = get_print_string_dir(wd, indent=pre_indent)
    lines.append(PrettyStruct(s, wd)) 

    if level == MAX_DEPTH:
        lines.append(PrettyStruct(post_indent + '|-- ...', None))
        return lines

    files = [] 
    dirs = [] 

    for f in os.listdir(wd):
        if f.startswith('.'):
            if LIST_ALL == 0:
                continue
        
        if f.endswith('~'):
            if IGNORE_BACKUPS:
                continue

        fs = os.path.realpath(wd + '/' + f)
        if os.path.isdir(fs):
            dirs.append(fs)
        elif os.path.isfile(fs):
            files.append(fs)

    if LIST_ALL == 2:
        lines.append(PrettyStruct(post_indent + '|-- .', None))
        lines.append(PrettyStruct(post_indent + '|-- ..', None))

    for f in files:
        s = get_print_string_file(f, indent=post_indent)
        lines.append(PrettyStruct(s, f))

    for d in dirs:
        lines.extend(print_tree(os.path.realpath(d), level=level+1))

    if len(dirs) == 0 and len(files) == 0:
        lines.append(PrettyStruct(post_indent + '|-- ..', None))
    
    return lines
