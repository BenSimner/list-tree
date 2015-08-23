from setuptools import setup

setup(
    name = 'list-tree'
    , version = '0.4'
    , packages = ['tree']
    , install_requires = ['nose', 'docopt']
    , entry_points = '''
        [console_scripts]
        lt = tree.main:main
    '''
)
