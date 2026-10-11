#!/bin/bash

. ./.env

./transcribe_week.py --week $1
./describe_images.py --week $1
./summary.py --week $1
