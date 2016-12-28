#!/bin/sh

FN_DATA="serialbatt-data-charging-oem-m2-1.txt serialbatt-data-charging-oem-m2-2.txt serialbatt-data-charging-powerextra-r1-m1-1.txt"
FN_DATA="serialbatt-data-charging-oem-m2-3.txt"

# pacman -S inotify-tools gnuplot
# apt-get install inotify-tools gnuplot
if inotifywait -e modify ${FN_DATA}; then
    echo "plotting ..."
    date
    ./serialbatt-plotfig.sh
    date
    echo "ploting done!"
fi

