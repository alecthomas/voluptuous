import io
import sys

from setuptools import setup

sys.path.insert(0, '.')
version = __import__('voluptuous').__version__


with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='voluptuous',
    url='https://github.com/alecthomas/voluptuous',
    download_url='https://pypi.python.org/pypi/voluptuous',
    version=version,
    description='Python data validation library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='BSD-3-Clause',
    platforms=['any'],
    packages=['voluptuous'],
    package_data={
        'voluptuous': ['py.typed'],
    },
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    python_requires=">=3.8",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ]
)
