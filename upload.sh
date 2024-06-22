#!/bin/bash

set -e

source /home/felipe/.profile
source /home/felipe/.bashrc


cd /home/felipe/toji_everyday
pyenv activate toji_everyday
pyenv exec python main.py >> instagram_summary.log