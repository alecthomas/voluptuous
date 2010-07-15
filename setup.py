try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='voluptuous',
    url='http://github.com/alecthomas/voluptuous',
    download_url='http://pypi.python.org/pypi/voluptuous',
    version='0.1',
    description=open('README').readlines()[0],
    long_description=open('README').read(),
    license='BSD',
    platforms=['any'],
    py_modules=['voluptuous'],
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    install_requires = [
        'setuptools >= 0.6b1',
    ],
    )
