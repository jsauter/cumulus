#!/bin/bash

clear
echo `date`
echo "Starting Tests . . . "

py.test -s tests/unit --color=yes -v # --cov=lib --cov-report term-missing:skip-covered
export CI_TEST_RESULT=$?

#don't bother linting if tests fail
#test $? -ne 0 && exit 1
echo '-- flake8 started ---'
flake8 cumulus tests
export CI_FLAKE_RESULT=$?
echo '-- flake8 finished --'
exit $CI_FLAKE_RESULT
