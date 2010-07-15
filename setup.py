try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
sys.path.insert(0, '.')
version = __import__('voluptuous').__version__
long_description = open('README.rst').read()
description = long_description.splitlines()[0].strip()


setup(
    name='voluptuous',
    url='http://github.com/alecthomas/voluptuous',
    download_url='http://pypi.python.org/pypi/voluptuous',
    version=version,
    description=description,
    long_description=long_description,
    license='BSD',
    platforms=['any'],
    py_modules=['voluptuous'],
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    install_requires = [
        'setuptools >= 0.6b1',
    ],
    )
