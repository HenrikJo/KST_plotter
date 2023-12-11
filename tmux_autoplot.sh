#!/usr/bin/env bash
logfile="./tmux.log"
tmux capture-pane -pS - > ${logfile}
python3 plot_in_kst.py --file ${logfile}
