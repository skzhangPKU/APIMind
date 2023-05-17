#!/bin/bash
#删除当前路径下所有文件名字中的空格，以"-"代替
find . -type f -name "* *" -print |
while read name;
do
     echo "-------1----------";
     na=$(echo $name | tr ' ' '_')
     if [[ $name != $na ]]; then
     #echo $na;
     mv "$name" $na;
     fi
done