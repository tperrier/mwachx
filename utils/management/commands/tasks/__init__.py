from os.path import dirname, basename, isfile
import glob

# From: http://stackoverflow.com/questions/1057431/loading-all-modules-in-a-folder-in-python
# Add all python files in this directory to task_list
modules = glob.glob(dirname(__file__)+"/*.py")
task_list = [ basename(f)[:-3] for f in modules if isfile(f) and not basename(f).startswith('__')]
