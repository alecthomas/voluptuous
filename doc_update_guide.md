# Documentation Update Guide

Steps to update the documentation for the GitHub pages.

## Install Sphinx

Tested with version 7.0.1

```bash
pip install -U sphinx
```

## Checkout and merge

Checkout documentation branch `gh-pages` and merge the latest `master` version in.

```bash
git checkout gh-pages
git merge master
```

## Use Sphinx API Doc to generate the RST files

Run from the repo root folder. We are excluding everything from the `/test` folder as to not pollute the documentation with the tests.

```bash
sphinx-apidoc -o docs voluptuous "**/tests*" -f -M
```

## Generate the HTML files

In the `/docs` folder, run `make clean` to first clear the build outputs and then `make html` to generate the new HTML files.

```bash
make clean
make html
```

## Push the changes

```
git push
```