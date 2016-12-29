#!/bin/sh

FN_DATA="nxvlogbatt-data-charging-oem-m2-1.txt nxvlogbatt-data-charging-oem-m2-2.txt nxvlogbatt-data-charging-powerextra-r1-m1-1.txt"
FN_DATA="nxvlogbatt-data-charging-oem-m2-3.txt"

# pacman -S inotify-tools gnuplot
# apt-get install inotify-tools gnuplot
if inotifywait -e modify ${FN_DATA}; then
    echo "plotting ..."
    date
    ./nxvlogbatt-plotfig.sh
    date
    echo "ploting done!"
fi

