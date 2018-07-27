try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
import os
import atexit
sys.path.insert(0, '.')
version = __import__('voluptuous').__version__

import pypandoc
long_description = pypandoc.convert('README.md', 'rst')
with open('README.rst', 'wb') as f:
    f.write(long_description.encode('utf-8'))
atexit.register(lambda: os.unlink('README.rst'))

description = long_description.splitlines()[0].strip()


setup(
    name='voluptuous',
    url='https://github.com/alecthomas/voluptuous',
    download_url='https://pypi.python.org/pypi/voluptuous',
    version=version,
    description=description,
    long_description=long_description,
    license='BSD',
    platforms=['any'],
    packages=['voluptuous'],
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
