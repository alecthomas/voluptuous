try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
import os
import atexit
sys.path.insert(0, '.')
version = __import__('morphology').__version__

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
    with open('README.rst', 'wb') as f:
        f.write(long_description.encode('utf-8'))
    atexit.register(lambda: os.unlink('README.rst'))
except (ImportError, OSError):
    print('WARNING: Could not locate pandoc, using Markdown long_description.')
    with open('README.md') as f:
        long_description = f.read()

description = long_description.splitlines()[0].strip()


setup(
    name='morphology',
    url='https://github.com/nathanielford/morphology',
    download_url='https://pypi.python.org/pypi/morphology',
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='BSD',
    platforms=['any'],
    packages=['morphology'],
    author='Nathaniel Ford',
    author_email='nathaniel.ford@eryri.org',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
