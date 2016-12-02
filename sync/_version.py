from subprocess import check_output

__version__ = '1.6.0b4'

try:
    git_version = check_output(['git', 'log']).split('\n')[0].split(' ')[1]
except:
    git_version = 'N/A'
