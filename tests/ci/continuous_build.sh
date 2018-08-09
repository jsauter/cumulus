#!/bin/bash
#
# if [ ! -d '.git' ]; then
#   echo "this script works when run from the root directory."
#   echo "please run from the root like this:  ./ci/continuous_build.sh"
#   exit 1
# fi

#if which fswatch >/dev/null; then
#    echo This build is triggered on any changes to the ./root directory.
#    echo Save a file to execute your first build.
#    echo
#    echo CTRL - C to exit
#else
#    echo fswatch not found.
#    echo Please install homebrew, and then brew install fswatch
#fi
#
#fswatch -e ".*" -i "\\.py$" -i "\\.yaml$"  -x -o .. | xargs -n1 ./tests/ci/unit.sh || echo "failed.  Please restart this script."

#The above was deprecated for pytest-watch.
# add this line to -afterrun to see diff output as well
# printf "\nChanges:\n$(git diff --stat) \n "'

if [[ `uname` == 'Darwin' ]]; then
    ptw -v \
        -c \
        --afterrun 'echo "--flake8--"; flake8 cumulus tests ; printf "$? \n"' \
        --onfail "osascript -e 'display notification \"CI Tests Failed \" with title \"Test Result\"'"
fi
