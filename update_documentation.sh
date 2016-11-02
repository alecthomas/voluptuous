#!/usr/bin/env bash
git checkout gh-pages
git merge master
pip install -r requirements.txt
sphinx-apidoc -o  docs -f voluptuous