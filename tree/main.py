# main.py - Entry-point for `list-tree'
# author: Ben Simner 
'''Implements list-tree

Attempts to imitate ls in operation and arguments, but instead displays as a tree-view
'''

import os
import time
import math
import stat
import pwd
import grp
from docopt import docopt
from collections import namedtuple

def main():
    doc = '''
Usage:
    lt [--color=<when>] [--max-depth=<depth>] [-aABFhlR] [<dir>]
Options: 
    <dir>                   Directory to read from 
    --color=<when>          Colorize the output, can be 'never', 'auto' or 'always' [default: always]
    --max-depth=<depth>     Maximum depth to branch to [default: 3]
    -a --all                Do not ignore entries starting with .
    -A --almost-all         Like -a except do not list implied . and ..
    -B --ignore-backups     Do not list entries ending with ~
    -F --classify           Append indicator to entries
    -h --human-readable     With -l, print human-readable sizes
    -l                      Use long-list format
    -R --no-recursive       Do not recursively print directories
'''
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
    global NO_RECUR
    global CLASSIFY

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
    NO_RECUR = argv.get('--no-recursive', False)
    CLASSIFY = argv.get('--classify', False)

    if COLOR_MODE == 'never':
        bcolors.no_col()

    
    if LONG_LIST:
        lines = print_tree(os.path.realpath(cwd))
        print_long_list_fmt(lines)
    else:
        lines = print_tree(os.path.realpath(cwd))
        for struct in lines:
            print(struct.pretty_str)

def print_long_list_fmt(lines):
    # generate prefixes
    prefix_strs = []
    max_lens = [0]*7
    for struct in lines:
        if struct.path:
            prefixs = []
            attrs = get_attributes(struct.path)

            prefix = attrs.file_mode
            prefixs.append(prefix)
            if len(prefix) > max_lens[0]:
                max_lens[0] = len(prefix)

            prefix = str(attrs.hlink_count)
            prefixs.append(prefix)
            if len(prefix) > max_lens[1]:
                max_lens[2] = len(prefix)

            prefix = pwd.getpwuid(attrs.user_id).pw_name
            prefixs.append(prefix)
            if len(prefix) > max_lens[3]:
                max_lens[3] = len(prefix)

            prefix = grp.getgrgid(attrs.group_id).gr_name
            prefixs.append(prefix)
            if len(prefix) > max_lens[4]:
                max_lens[4] = len(prefix)

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
            if len(prefix) > max_lens[5]:
                max_lens[5] = len(prefix)
            
            prefix = '' 
            prefix += time.strftime('%b %d %Y %H:%M', time.gmtime(attrs.last_modified))
            prefixs.append(prefix)
            if len(prefix) > max_lens[6]:
                max_lens[6] = len(prefix)

            prefix_strs.append(prefixs)
        else:
            prefix_strs.append(['', '', ''])

    for prefixs, struct in zip(prefix_strs, lines):
        prefix = ''
        for p, max_len in zip(prefixs, max_lens):
            prefix += p + ' '*(3 + max_len - len(p))
        print(prefix + ' ' + struct.pretty_str)

class bcolors:
    '''ANSI escape sequences'''
    HEADER = '\033[95m'
    CYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def no_col():
        '''Disables ANSI escape sequencies'''
        bcolors.HEADER = ''
        bcolors.BLUE = ''
        bcolors.GREEN = ''
        bcolors.WARNING = ''
        bcolors.FAIL = ''
        bcolors.ENDC = ''
        bcolors.BOLD = ''
        bcolors.UNDERLINE = ''


Attributes = namedtuple('FileAttributes', ['size', 
                                            'executable', 
                                            'file_mode',
                                            'islink',
                                            'ispipe',
                                            'isdoor',
                                            'issock',
                                            'hlink_count',
                                            'user_id',
                                            'group_id',
                                            'last_modified'])

def get_attributes(path):
    st = os.stat(path)

    return Attributes(
        st.st_size,
        os.access(path, os.X_OK),
        stat.filemode(st.st_mode),
        os.path.islink(path),
        stat.S_ISFIFO(st.st_mode),
        stat.S_ISDOOR(st.st_mode),
        stat.S_ISSOCK(st.st_mode),
        st.st_nlink,
        st.st_uid,
        st.st_gid,
        st.st_mtime
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
        col = bcolors.BOLD + bcolors.GREEN
        x += '*'
    if attr.islink:
        col = bcolors.BOLD + bcolors.CYAN
        x += '@'
    if attr.isdoor:
        x += '>'
    if attr.issock:
        x += '='
    if attr.ispipe:
        x += '|'
            
    s += col + f + bcolors.ENDC
    if CLASSIFY:
        s += bcolors.BOLD + x + bcolors.ENDC

    return s

def get_print_string_dir(path, indent=''):
    '''returns the printstring for some dir with realpath 'path'
    includes ANSI color tags 
    given some indent
    '''
    s = indent
    d = os.path.basename(path)

    x = ''

    attr = get_attributes(path)
    col = bcolors.BOLD + bcolors.BLUE

    if attr.islink:
        col = bcolors.BOLD + bcolors.CYAN
        x += '@'
    if attr.isdoor:
        x += '>'
    if attr.issock:
        x += '='
    if attr.ispipe:
        x += '|'
    
    if x == '':
        x += '/'

    s += col + d + bcolors.ENDC

    if CLASSIFY:
        s += x

    return s

PrettyStruct = namedtuple('File', ['pretty_str', 'path'])

def print_tree(wd, level=0, indent='', indent_char=' ', last_dir=False):
    '''Returns pretty-prints tree structure starting at 'wd' i.e.:
        wd/
          |-- file1
          |-- file2*
          |-- dir@
          |-- |-- file3
          |-- |-- file4*
          |-- other_dir/
              |-- file5
              |-- file5

    on each dir the level increases by 1
    '''
    lines = []

    # take indent up to this level and add a single level of indent
    if not last_dir and level > 0: 
        post_indent = indent + '|' + indent_char*2
    else:
        post_indent = indent + indent_char*2
    
    s = get_print_string_dir(wd, indent=indent + '|-- ')
    lines.append(PrettyStruct(s, wd)) 

    if level == MAX_DEPTH:
        return lines

    # with NO_RECUR flag only write top-level directory contents
    if NO_RECUR and level > 0:
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

        fs = wd + '/' + f
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
        last = False
        if d == dirs[-1]:
            last = True
        lines.extend(print_tree(d,
                                level=level+1,
                                indent=post_indent,
                                indent_char=indent_char,
                                last_dir=last))

    if len(dirs) == 0 and len(files) == 0:
        lines.append(PrettyStruct(post_indent + '|-- ..', None))
    
    return lines