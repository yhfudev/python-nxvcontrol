#!/bin/bash

PNGSIZE="1024,768"
#PNGSIZE="800,600"
PNGSIZE="1800,900"

EPSSIZE="8,4"

function plot_charging() {
    local PARAM_PREFIX=$1
    shift
    local PARAM_VBATRAT=$1
    shift
    local PARAM_XRANGE=$1
    shift

    FN_DATA="${PARAM_PREFIX}.txt"
    # figure -- charging current, voltage/% and tempreture
    FN_GPOUT="fig-${PARAM_PREFIX}"
    cat << EOF > "${FN_GPOUT}.gp"
# set terminal png transparent nocrop enhanced size 450,320 font "arial,8" 
set terminal png size ${PNGSIZE}
set output "${FN_GPOUT}.png"

#set key left bottom
#set key center bottom
#set key right bottom
set key center

set autoscale x
#set autoscale x2
set autoscale y
#set autoscale y2
set yrange [-400<*:*<2500]
set y2range [0<*:10<*<100]
EOF

    if [ ! "${PARAM_XRANGE}" = "" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
set xrange [${PARAM_XRANGE}]
EOF
    fi

    cat << EOF >> "${FN_GPOUT}.gp"
#set xtics 0,.5,10
set ytics -400,100,2500
set y2tics
set grid x y y2

set xlabel 'Time (seconds)'
set ylabel 'Current (mA)'
set y2label 'Voltage (V), %, Temp (°C)'

EOF

    if [ "${PARAM_VBATRAT}" = "1" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
# x -- time
# y -- current
# y2 -- temperature, voltage, %, voltage/%
plot '${FN_DATA}' using 1:(\$7*3)     title 'VBattV*3' with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$8*3)     title 'VExtV*3'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$2/-1)    title 'Battery Current' with lines axes x1y1 \
   , '${FN_DATA}' using 1:9           title 'FuelPercent (%)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:4           title 'BatteryTemp0InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:5           title 'BatteryTemp1InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$7*400/\$9) title 'VBattV*400/%'  with lines axes x1y2
EOF
    else
        cat << EOF >> "${FN_GPOUT}.gp"
# x -- time
# y -- current
# y2 -- temperature, voltage, %, voltage/%
plot '${FN_DATA}' using 1:(\$7*3)     title 'VBattV*3' with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$8*3)     title 'VExtV*3'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$2/-1)    title 'Battery Current' with lines axes x1y1 \
   , '${FN_DATA}' using 1:9           title 'FuelPercent (%)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:4           title 'BatteryTemp0InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:5           title 'BatteryTemp1InC (°C)' with lines axes x1y2
EOF
   #, '${FN_DATA}' using 1:11          title 'Charging Current'     with lines axes x1y1
    fi

    cat << EOF >> "${FN_GPOUT}.gp"
#set terminal pdf color solid lw 1 size 5.83,4.13 font "cmr12" enh
#set pointsize 1
#set output "${FN_GPOUT}.pdf"
set terminal postscript eps size ${EPSSIZE} color enhanced
set output "${FN_GPOUT}.eps"
replot

EOF

    gnuplot "${FN_GPOUT}.gp"
}

LIST_DATA=(
    # <prefix>, <1: plot VBattV*400/%>,  <comments>
    "serialbatt-data-charging-new-1,1,new battery first charging"
    "serialbatt-data-charging-new-2,1,new battery second charging"
    "serialbatt-data-charging-new-3,1,new battery third charging, after refresh with neatoctrl (deep recharge), there's a dust box install at the middle of charging"
    "serialbatt-data-charging-new-4,1,new battery 4th charging"
    "serialbatt-data-standby-new-2,1,new battery standby after second charging"
    "serialbatt-data-charging-old-1,0,old battery first charging"
    "serialbatt-data-charging-old-2,0,old battery second charging"
    "serialbatt-data-charging-old-3,0,old battery third charging"
    #"serialbatt-data-standby-old-1,0,new battery standby after first charging"
    )
LIST_DATA=(
    "serialbatt-data-charging-new-4,1,new battery 4th charging"
    #"serialbatt-data-charging-old-1,0,old battery first charging"
    #"serialbatt-data-charging-old-2,0,old battery second charging"
    #"serialbatt-data-charging-old-3,0,old battery third charging"
    )
function do_work() {
    local i=0
    while (( ${i} < ${#LIST_DATA[*]} )); do
        local LINE1="${LIST_DATA[${i}]}"
        local PREFIX1=$(echo "${LINE1}" | awk -F, '{print $1}')
        local VBATRAT=$(echo "${LINE1}" | awk -F, '{print $2}')
        plot_charging "${PREFIX1}" "${VBATRAT}" #"0:*<50"
        i=$((i + 1))
    done
}

do_work
