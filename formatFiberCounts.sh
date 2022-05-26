#!/bin/bash

# Usage: 
# Produce check report. Then run: 
# source formatFiberCounts.sh [CHECK FILE] [OUTPUT FILE]

rm -f temp
awk '/^Layer .*/ || /^MB       Status/,/===/' $1 > $2
sed -i '' -e '/^$/d' -e '/^All.*$/d' -e '/^===.*$/d' -e '/^MB.*$/d' -e 's/^Layer //' -e 's/ has.*$//' $2
awk -F' ' '{print $1 "\t" $7 "\t" $10}' $2 > temp && mv temp $2
echo -e "plane\tMB\tDlpGBT\tTlpGBT" > temp
plane="-1"
while read line; do
  if [[ "$line" =~ ^[[:digit:]]+$ ]]; then
    plane="$line"
    continue
  fi
  echo -e "$plane\t$line" >> temp
done < $2
mv temp $2
