#!/usr/bin/env bash

# Merge pushes to development branch to stable branch
if [ ! -n $2 ] ; then
    echo "Usage: merge.sh <username> <password>"
    exit 1;
fi

GIT_USER="$1"
GIT_PASS="$2"

# Specify the development branch and stable branch names
FROM_BRANCH="master"
TO_BRANCH="gh-pages"

# Needed for setting identity
git config --global user.email "tusharmakkar08@gmail.com"
git config --global user.name "Tushar Makkar"
git config --global push.default "simple"

# Get the current branch
export PAGER=cat
CURRENT_BRANCH=$(git log -n 1 --pretty=%d HEAD | cut -d"," -f3 | cut -d" " -f2 | cut -d")" -f1)
echo "current branch is '$CURRENT_BRANCH'"

# Create the URL to push merge to
URL=$(git remote -v | head -n1 | cut -f2 | cut -d" " -f1)
echo "Repo url is $URL"
PUSH_URL="https://$GIT_USER:$GIT_PASS@${URL:8}"

git remote set-url origin ${PUSH_URL}

echo "Checking out $FROM_BRANCH..." && \
git fetch origin ${FROM_BRANCH}:${FROM_BRANCH} && \
git checkout ${FROM_BRANCH}


echo "Checking out $TO_BRANCH..." && \
# Checkout the latest stable
git fetch origin ${TO_BRANCH}:${TO_BRANCH} && \
git checkout ${TO_BRANCH} && \

# Merge the dev into latest stable
echo "Merging changes..." && \
git merge ${FROM_BRANCH} && \

# Push changes back to remote vcs
echo "Pushing changes..." && \
git push origin gh-pages &> /dev/null && \
echo "Merge complete!" || \
echo "Error Occurred. Merge failed"

export PYTHONPATH=${PYTHONPATH}:$(pwd):$(pwd)/voluptuous

pip install -r requirements.txt && sphinx-apidoc -o  docs -f voluptuous &&
cd docs && make html ||
echo "Sphinx not able to generate HTML"

git status && git add . &&
git commit -m "Auto updating documentation from $CURRENT_BRANCH" &&
git push origin gh-pages  &> /dev/null && echo "Documentation pushed"
