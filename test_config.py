from core.config import paths
import sys

infile_name = ''
if sys.platform.startswith('win'):
    infile_name = 'walkoff_windows_template.conf'
elif sys.platform.startswith('linux'):
    infile_name = 'walkoff_linux_template.conf'

with open(infile_name, 'r') as infile, open('WALKOFF.conf', 'w') as outfile:
    for line in infile:
        if 'PATH' in line:
            line = line.replace('PATH', paths.wsgi_config_path)
        outfile.write(line)
