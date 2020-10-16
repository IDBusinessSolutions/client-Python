import setup
import shutil
import os
import glob
import robot.libdoc as libdoc

#name and package dir
library_name = 'reportportal_client'
packages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Packages'))

#version
file = os.path.join(os.path.dirname(__file__), library_name, 'version.py')
exec(open(file).read())

#generate the package
setup.run_setup(VERSION, ['sdist'])

#copy package to packages directory
doc_files = glob.iglob(os.path.join(os.path.dirname(__file__), 'dist/*.*'))
for file in doc_files:
    if os.path.isfile(file):
        shutil.copy(file, packages_dir)
        
#tidy up build folders
shutil.rmtree('dist')
egg_info_folders = glob.iglob(os.path.join(os.path.dirname(__file__), 'src/*.egg-info'))
for folder in egg_info_folders:
    shutil.rmtree(folder)
    
#build confirmation message
print("Build successful")
