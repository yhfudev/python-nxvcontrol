#!/bin/sh

FN_DATA=serialbatt-data-charging-old.txt
FN_DATA=serialbatt-data-standby-old.txt
FN_DATA=serialbatt-data-charging-new.txt
FN_DATA=serialbatt-data-standby-new.txt

PNGSIZE="1024,768"
#PNGSIZE="800,600"
PNGSIZE="1800,600"



# figure -- charging current and voltage
FN_GPOUT="fig-iv"
cat << EOF > "${FN_GPOUT}.gp"
# set terminal png transparent nocrop enhanced size 450,320 font "arial,8" 
set terminal png size ${PNGSIZE}
set output "${FN_GPOUT}.png"

#set key left bottom
#set key center bottom
#set key right bottom
set key center

set autoscale y
set autoscale y2
set autoscale x
#set autoscale x2

set y2tics
set grid x y y2

set xlabel 'Time (seconds)'
set ylabel 'Current (mA)'
set y2label 'Voltage (V)'

plot '${FN_DATA}' using 1:7           title 'VBattV'   with lines axes x1y2 \
   , '${FN_DATA}' using 1:8           title 'VExtV'    with lines axes x1y2 \
   , '${FN_DATA}' using 1:2           title 'Battery Current'  with lines axes x1y1 \
   #, '${FN_DATA}' using 1:11         title 'Charging Current' with lines axes x1y1 \


#set terminal pdf color solid lw 1 size 5.83,4.13 font "cmr12" enh
#set pointsize 1
#set output "${FN_GPOUT}.pdf"
set terminal postscript eps color enhanced
set output "${FN_GPOUT}.eps"
replot

EOF

gnuplot "${FN_GPOUT}.gp"




# figure -- charging current, voltage/% and tempreture
FN_GPOUT="fig-it"
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
set y2range [10:100]

set y2tics
set grid x y y2

set xlabel 'Time (seconds)'
set ylabel 'Current (mA)'
set y2label 'Voltage (V), %, Temp (°C)'

# x -- time
# y -- current
# y2 -- temperature, voltage, %, voltage/%
plot '${FN_DATA}' using 1:7           title 'VBattV' with lines axes x1y2 \
   , '${FN_DATA}' using 1:8           title 'VExtV'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:2           title 'Battery Current' with lines axes x1y1 \
   , '${FN_DATA}' using 1:9           title 'FuelPercent (%)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:(\$7*400/\$9) title 'VBattV*400/%'  with lines axes x1y2 \
   , '${FN_DATA}' using 1:4           title 'BatteryTemp0InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:5           title 'BatteryTemp1InC (°C)' with lines axes x1y2 \
   #, '${FN_DATA}' using 1:11          title 'Charging Current'     with lines axes x1y1 \

#set terminal pdf color solid lw 1 size 5.83,4.13 font "cmr12" enh
#set pointsize 1
#set output "${FN_GPOUT}.pdf"
set terminal postscript eps color enhanced
set output "${FN_GPOUT}.eps"
replot

EOF

gnuplot "${FN_GPOUT}.gp"

exit 0



FN_GPOUT="fig-temp"
cat << EOF > "${FN_GPOUT}.gp"
# set terminal png transparent nocrop enhanced size 450,320 font "arial,8" 
set terminal png size ${PNGSIZE}
set output "${FN_GPOUT}.png"

#set key left bottom
#set key center bottom
set key right bottom

set autoscale y
set autoscale y2
set autoscale x
#set autoscale x2

set y2tics
set grid x y y2

set xlabel 'Time (sec)'
set ylabel 'Batt Capacity (%)'
set y2label 'Temp (°C)'

plot '${FN_DATA}' using 1:9 title 'FuelPercent (%)'      with lines axes x1y1 \
   , '${FN_DATA}' using 1:4 title 'BatteryTemp0InC (°C)' with lines axes x1y2 \
   , '${FN_DATA}' using 1:5 title 'BatteryTemp1InC (°C)' with lines axes x1y2 \

#set terminal pdf color solid lw 1 size 5.83,4.13 font "cmr12" enh
#set pointsize 1
#set output "${FN_GPOUT}.pdf"
set terminal postscript eps color enhanced
set output "${FN_GPOUT}.eps"
replot

EOF

gnuplot "${FN_GPOUT}.gp"



