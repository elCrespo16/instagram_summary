#!/bin/bash

set -e

source /home/felipe/.profile
source /home/felipe/.bashrc


cd /home/felipe/instagram_summary
pyenv activate instagram_summary
pyenv exec python main.py >> instagram_summary.log