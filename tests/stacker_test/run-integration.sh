#!/usr/bin/env bash

stacker build conf/test.env stacker.yaml
stacker destroy conf/test.env stacker.yaml --force
