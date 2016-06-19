#!/usr/bin/env python3
# main.py - Entry-point for `list-tree'
# author: Ben Simner
'''list-tree

Usage:
    lt [options] [<dir>]

Options:
    <dir>                   Directory to read from
    -c --color=<when>          Colorize the output, can be 'never', 'auto' or 'always' [default: always]
    -a --all                Do not ignore entries starting with .
    -A --almost-all         Like -a except do not list implied . and ..
    -B --ignore-backups     Do not list entries ending with ~
    -d --max-depth=<depth>  Maximum depth to branch to [default: 2]
    -F --classify           Append indicator to entries
    -g --gitignore          Respect .gitignore and don't print out ignored files
    -h --human-readable     With -l, print human-readable sizes
    -l                      Use long-list format
    -R --no-recursive       Do not recursively print directories
'''

import os
import time
import math
import stat
import subprocess
from docopt import docopt
from collections import namedtuple

class Symbols:
    CROSS = '+'
    VLINE = '|'
    VLINER = '|'
    HLINE = '-'

def main():
    args = docopt(__doc__)
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
    global RESPECT_GITIGNORE

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
    RESPECT_GITIGNORE = argv.get('--gitignore', False)

    if COLOR_MODE == 'never':
        bcolors.no_col()

    try:
        get_attributes(cwd)
    except FileNotFoundError:
        head, d = os.path.split(os.path.abspath(cwd))
        s = '{}{}{}/'.format(bcolors.BLUE + bcolors.BOLD, d, bcolors.ENDC)
        print('{} not found'.format(s))
        return

    if LONG_LIST:
        lines = print_tree(os.path.realpath(cwd))
        print_long_list_fmt(lines)
    else:
        lines = print_tree(os.path.realpath(cwd))
        pretty = struct_prettifier()
        next(pretty)

        for struct in lines:
            print(pretty.send(struct))

def print_long_list_fmt(lines):
    '''Prints a long-list format given by generator 'lines'

    in format [drwxrwxrwx](10) [hlink_count](3) [user_id](5) [group_id](5) [size](10) [time](15) [pretty_str](...)
    '''

    pretty = struct_prettifier()
    next(pretty)

    for struct in lines:
        attrs = get_attributes(struct.path)
        line = []

        line.append(attrs.file_mode.ljust(11))
        line.append(str(attrs.hlink_count).ljust(3))
        line.append(str(attrs.user_id).ljust(5))
        line.append(str(attrs.group_id).ljust(5))

        size = ''
        if not HUMAN_READABLE:
            size = str(attrs.size) + 'B'
        else:
            if attrs.size <= 0:
                size = '0B'
            else:
                log = round(math.log(attrs.size, 10))
                if log < 3:
                    size = str(attrs.size) + 'B'
                elif log < 6:
                    size = '%.1f' % (attrs.size / 1024) + 'KB'
                elif log < 9:
                    size = '%.1f' % (attrs.size / (1024 ** 2)) + 'MB'
                else:
                    size = '%.1f' % (attrs.size / (1024 ** 3)) + 'GB'
        line.append(size.ljust(10))
        line.append(time.strftime('%b %d %Y %H:%M', time.gmtime(attrs.last_modified)).ljust(15))
        line.append(pretty.send(struct))

        print(' '.join(line))

def struct_prettifier():
    s = ''
    open_folds = []
    while True:
        struct = yield s

        indent = ''
        _opens = len(open_folds)

        for i, x in enumerate(open_folds):
            if i == _opens - 1:
                if struct.directory:
                    indent += ' ' * 2 + Symbols.CROSS
                else:
                    indent += ' ' * 2 + Symbols.VLINE
            else:
                indent += ' ' * 2 + Symbols.VLINE

        # dropped out of directory
        while open_folds:
            last_open = open_folds[-1]
            if struct.depth < last_open:
                open_folds.pop()
            else:
                break

        if struct.directory:
            # jumped into directory
            if not open_folds or open_folds[-1] != struct.depth - 1:
                open_folds.append(struct.depth + 1)

        s = '{}{} {}'.format(indent, Symbols.HLINE * 2, struct.name)
        if struct.permission_failure:
            s += ' {}[PermissionDenied]{}'.format(bcolors.BOLD + bcolors.FAIL, bcolors.ENDC)

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
        bcolors.CYAN = ''
        bcolors.BLUE = ''
        bcolors.GREEN = ''
        bcolors.WARNING = ''
        bcolors.FAIL = ''
        bcolors.ENDC = ''
        bcolors.BOLD = ''
        bcolors.UNDERLINE = ''


Attributes = namedtuple(
    'FileAttributes',
    [
        'size',
        'executable',
        'file_mode',
        'islink',
        'ispipe',
        'isdoor',
        'issock',
        'hlink_count',
        'user_id',
        'group_id',
        'last_modified'
    ])

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
        st.st_mtime,
    )

def file_ignored(path):
    '''Returns `True` if file on 'path' is ignored by source control software
    i.e. disallowed by .gitignore files
    '''

    try:
        p = subprocess.Popen(['git', 'check-ignore', '-q', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exitcode = p.wait()
        if exitcode == 0:
            return True
        return False
    except:
        # assume out of repo
        # or not-found git
        return False

def get_print_string_file(path, indent=''):
    '''returns the printstring for some file with realpath 'path'
    includes ANSI color tags
    given some indent
    '''
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

    s = col + f + bcolors.ENDC
    if CLASSIFY:
        s += x + bcolors.ENDC

    return s

def get_print_string_dir(path):
    '''returns the printstring for some dir with realpath 'path'
    includes ANSI color tags
    given some indent
    '''
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

    s = col + d + bcolors.ENDC

    if CLASSIFY:
        s += x

    return s

File = namedtuple('File', ['name', 'depth', 'directory', 'permission_failure', 'path'])

def print_tree(wd, depth=0, last_dir=False):
    '''Returns a generator represneting  pretty-prints tree structure starting at 'wd' i.e.:
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

    s = get_print_string_dir(wd)

    if depth == MAX_DEPTH:
        raise StopIteration

    # with NO_RECUR flag only write top-level directory contents
    if NO_RECUR and depth > 0:
        raise StopIteration

    files = []
    dirs = []

    try:
        l = os.listdir(wd)
        yield File(s, depth, True, False, wd)

        for f in l:
            if f.startswith('.'):
                if not LIST_ALL:
                    continue

            if f.endswith('~'):
                if IGNORE_BACKUPS:
                    continue

            fs = wd + '/' + f

            if RESPECT_GITIGNORE:
                if file_ignored(fs):
                    continue

            if os.path.isdir(fs):
                dirs.append(fs)
            elif os.path.isfile(fs):
                files.append(fs)
    except PermissionError:
        yield File(s, depth, True, True, wd)
        raise StopIteration

    if LIST_ALL == 2:
        yield File('.', depth + 1, True, False, wd)
        yield File('..', depth + 1, True, False, wd)

    for f in files:
        s = get_print_string_file(f)
        yield File(s, depth + 1, False, False, f)

    for d in dirs:
        yield from print_tree(
            d,
            depth=depth + 1)

    if len(dirs) == 0 and len(files) == 0 and not LIST_ALL:
        yield File('..', depth + 1, True, False, wd)

if __name__ == '__main__':
    main()  # for testing
