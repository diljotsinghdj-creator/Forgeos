#!/bin/bash
export SHEETS=/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/s200
mkdir -p $SHEETS
mapfile -t Q < queries.txt
n=${#Q[@]}
for ((k=0; k<n; k+=10)); do
  name=p$(printf %02d $((k/10)))
  [ -f $SHEETS/$name.jpg ] && continue
  for t in 1 2 3; do
    python3 pick.py $name "${Q[@]:$k:10}" && break
    sleep 40
  done
  sleep 12
done
echo done
