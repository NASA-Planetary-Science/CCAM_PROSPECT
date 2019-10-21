#!/bin/bash

virtualenv env
source env/bin/activate
conda install --file requirements.txt

