# list-tree
Python command-line utility to list files like 'ls' but in a tree format.

Usage:
    ```lt [-aABFhlR --color=<when> --max-depth=<depth>] [<dir>]
    ```

Options:

    <dir>                   Directory to read from [default: .]
    --color=<when>          Colorize the output, can be 'never', 'auto' or 'always' [default: always]
    --max-depth=<depth>     Maximum depth to branch to [default: 3]
    -a --all                Do not ignore entries starting with .
    -A --almost-all         Like -a except do not list implied . and ..
    -B --ignore-backups     Do not list entries ending with ~
    -F --classify           Append indicator to entries
    -h --human-readable     With -l, print human-readable sizes
    -l                      Use long-list format
    -R --no-recursive       Do not recursively print directories

![lt -F output](https://dl.dropboxusercontent.com/u/92148800/ltf.png)
