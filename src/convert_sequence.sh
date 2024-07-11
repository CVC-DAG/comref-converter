#!/bin/bash

for x in /home/ptorras/Documents/Datasets/COMREF_10/*
do
    mxml=$(find "$x" -name '*.mxl')
    basename=$(basename -- "$mxml")
    directory=$(dirname -- "$mxml")
    # extension="${basename##*.}"
    filename="${basename%.*}"
    echo Converting "$x"
    python3 convert.py "$directory"/"$filename"_clean.mtn "$directory"/"$filename".seq
    if [ "$?" -ne 0  ]
    then
        echo "$x" >> failed.txt
    fi
done