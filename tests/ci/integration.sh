#!/bin/bash

clear
echo `date`
echo "Starting Tests . . . "
py.test --disable-warnings --durations=0 -n3 -s tests/integration
