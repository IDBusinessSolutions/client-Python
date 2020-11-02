"""Config for setup package client Python."""

import sys
from setuptools import setup, find_packages
from os.path import join, dirname

__version__ = '5.0.2'


def run_setup(version, scriptargs):
    setup(
        name='reportportal-client',
        packages=find_packages(),
        version=version,
        description='Python client for Report Portal v5.',
        author_email='SupportEPMC-TSTReportPortal@epam.com',
        url='https://github.com/reportportal/client-Python',
        license='Apache 2.0.',
        keywords=['testing', 'reporting', 'reportportal'],
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8'
        ],
        install_requires=['requests>=2.4.2', 'six'],
        zip_safe=False,
        script_args = scriptargs

    )
if __name__=="__main__":
    file = join(dirname(__file__),'reportportal_client', 'version.py')
    exec(open(file).read())
    run_setup(VERSION, sys.argv[1:])
