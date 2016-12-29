#!/bin/bash

PNGSIZE="1024,768"
#PNGSIZE="800,600"
PNGSIZE="1800,900"

EPSSIZE="8,4"

function plot_charging() {
    # the data file name prefix
    local PARAM_PREFIX=$1
    shift
    # 1 -- if draw VBattV*200/%
    local PARAM_VBATRAT=$1
    shift
    # set the x range
    local PARAM_XRANGE=$1
    shift
    # fig title
    local PARAM_TITLE=$1
    shift
    # fig comments
    local PARAM_COMMENTS=$1
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
#set key center
#set key right top
set key center top

set autoscale x
#set autoscale x2
set autoscale y
#set autoscale y2
#set yrange [-500<*:*<2500]
set yrange [-500:2000]
#set y2range [0<*:10<*<50]
set y2range [0:50]

# On both the x and y axes split each space in half and put a minor tic there
set mxtics 2
set mytics 2
set my2tics 2

# Line style for axes
# Define a line style (we're calling it 80) and set 
# lt = linetype to 0 (dashed line)
# lc = linecolor to a gray defined by that number
set style line 80 lt 0 lc rgb "#808080"

# Set the border using the linestyle 80 that we defined
# 3 = 1 + 2 (1 = plot the bottom line and 2 = plot the left line)
# back means the border should be behind anything else drawn
set border 3 back ls 80 

# Line style for grid
# Define a new linestyle (81)
# linetype = 0 (dashed line)
# linecolor = gray
# lw = lineweight, make it half as wide as the axes lines
set style line 81 lt 0 lc rgb "#808080" lw 0.5

# Draw the grid lines for both the major and minor tics
#set grid x y y2
set grid xtics
set grid ytics
set grid y2tics
set grid mxtics
#set grid mytics
#set grid my2tics

# Put the grid behind anything drawn and use the linestyle 81
set grid back ls 81
EOF

    if [ ! "${PARAM_XRANGE}" = "" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
set xrange [${PARAM_XRANGE}]
EOF
    fi


    if [ ! "${PARAM_TITLE}" = "" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
set title "${PARAM_TITLE}"
EOF
    fi

    if [ ! "${PARAM_COMMENTS}" = "" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
set label "${PARAM_COMMENTS}" at graph 1.05,-.065 right #first -1
#set label "${PARAM_COMMENTS}" at 2.5,0.5 tc rgb "white" font ",30" front
EOF
    fi

    cat << EOF >> "${FN_GPOUT}.gp"
#set xtics 0,.5,10
set ytics -500,50,2000 nomirror
set y2tics 0,1,50 nomirror #textcolor rgb "red"

set xlabel 'Time (seconds)'
set ylabel 'Current (mA)'
set y2label 'Voltage (V), %/10, Temp (°C)'

EOF

    if [ "${PARAM_VBATRAT}" = "1" ]; then
        cat << EOF >> "${FN_GPOUT}.gp"
# x -- time
# y -- current
# y2 -- temperature, voltage, %, voltage/%
plot '${FN_DATA}' using 1:7           title 'VBattV' with lines axes x1y2 \
   , '${FN_DATA}' using 1:8           title 'VExtV'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$2/-1)    title 'Battery Current (mA)' with lines axes x1y1 \
   , '${FN_DATA}' using 1:(\$9/10)    title 'FuelPercent (%/10)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:4           title 'BatteryTemp0InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:5           title 'BatteryTemp1InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$7*200/\$9) title 'VBattV*200/%'  with lines axes x1y2
EOF
    else
        cat << EOF >> "${FN_GPOUT}.gp"
# x -- time
# y -- current
# y2 -- temperature, voltage, %, voltage/%
plot '${FN_DATA}' using 1:7           title 'VBattV' with lines axes x1y2 \
   , '${FN_DATA}' using 1:8           title 'VExtV'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$2/-1)    title 'Battery Current (mA)' with lines axes x1y1 \
   , '${FN_DATA}' using 1:(\$9/10)    title 'FuelPercent (%/10)' with lines axes x1y2 \
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



# 2016-12-07 10: m2 upgrade to 3.4
LIST_DATA=(
    # <prefix>, <1: plot VBattV*400/%>, <brand>, <serial>, <comments>
    "nxvlogbatt-data-charging-mcnair-old-m2-1,0,McNair Ni-MH 7.2V 3200mAh for Neato XV x2,1,McNair battery old-in the machine-first charging-machine2-firmware 3.1"
    "nxvlogbatt-data-charging-mcnair-old-m2-2,0,McNair Ni-MH 7.2V 3200mAh for Neato XV x2,1,McNair battery old-in the machine-second charging-machine2-firmware 3.1"
    "nxvlogbatt-data-charging-mcnair-old-m2-3,0,McNair Ni-MH 7.2V 3200mAh for Neato XV x2,1,McNair battery old-in the machine-third charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-oem-m1-1,1,OEM Ni-MH 7.2V 3200mAh for Neato XV x2,1,OEM battery old-in the machine-first charging-machine1-firmware 3.1"
    "nxvlogbatt-data-charging-powerextra-r1-m2-1,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-first charging-machine2-firmware 3.1"
    "nxvlogbatt-data-charging-powerextra-r1-m2-2,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-second charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-powerextra-r1-m2-3,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-third charging-machine2-firmware 3.4-after refresh with neatoctrl (deep recharge), there's a dust box install at the middle of charging"
    "nxvlogbatt-data-charging-powerextra-r1-m2-4,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-4th charging-machine2-firmware 3.4-can only last 5min?"
    "nxvlogbatt-data-standby-powerextra-r1-m2-2,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-standby after second charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-oem-m2-1,1,OEM Ni-MH 7.2V 3200mAh for Neato XV x2,1,OEM battery old-in the machine-first charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-oem-m2-2,1,OEM Ni-MH 7.2V 3200mAh for Neato XV x2,1,OEM battery old-in the machine-second charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-oem-m2-3,1,OEM Ni-MH 7.2V 3200mAh for Neato XV x2,1,OEM battery old-in the machine-third charging-machine2-firmware 3.4"
    "nxvlogbatt-data-charging-powerextra-r1-m1-1,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round1-first charging-machine1-firmware 3.1"

    "nxvlogbatt-data-charging-powerextra-r2-m1-1,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round2-first charging-machine1-firmware 3.1" #TODO: the second round of battery, with old firmware and old hardware
    "nxvlogbatt-data-charging-powerextra-r2-m1-2,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round2-second charging-machine1-firmware 3.4" #TODO: the second round of battery, with firmware 3.4 and updated hardware(capacitors)
    "nxvlogbatt-data-charging-powerextra-r2-m2-1,1,Powerextra Ni-MH 7.2V 4000mAh for Neato XV x2,1,powerextra battery-round2-third charging-machine2-firmware 3.4" #TODO: the second round of battery, with firmware 3.4 and updated hardware(capacitors)
    )
LIST_DATA=(
    "nxvlogbatt-data-charging-oem-m2-3,1,OEM Ni-MH 7.2V 3200mAh for Neato XV x2,1,OEM battery old-in the machine-third charging-machine2-firmware 3.4"
    )
function do_work() {
    local i=0
    while (( ${i} < ${#LIST_DATA[*]} )); do
        local LINE1="${LIST_DATA[${i}]}"
        local PREFIX1=$(echo "${LINE1}" | awk -F, '{print $1}')
        local VBATRAT=$(echo "${LINE1}" | awk -F, '{print $2}')
        local BRAND=$(echo "${LINE1}" | awk -F, '{print $3}')
        local SERIAL=$(echo "${LINE1}" | awk -F, '{print $4}')
        local COMMENTS=$(echo "${LINE1}" | awk -F, '{print $5}')
        date
        plot_charging "${PREFIX1}" "${VBATRAT}" "" "Charging '${BRAND}' (${SERIAL})" "${COMMENTS}"
        date
        i=$((i + 1))
    done
}

do_work
