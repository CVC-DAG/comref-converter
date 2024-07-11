#!/bin/bash

for x in /home/ptorras/Documents/Datasets/COMREF_10/*
do
    rm "$x"/*.mtn
    rm "$x"/removed_on_cleanup.json
done