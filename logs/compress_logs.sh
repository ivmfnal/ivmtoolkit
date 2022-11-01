#!/bin/bash

compress_dir()
{
        echo compress_dir: $1 $2   pwd: `pwd`
	cd $1
        n=$2
	for f in *; do
                if [ -f $f ] && [ -f ${f}.1 ]; then
                        echo
			echo $f
			echo
			rm -f ${f}.${n}.gz
			i=$n
			while [ $i -gt 1 ]
			do
				j=$(($i-1))
				mv ${f}.${j}.gz ${f}.${i}.gz 2>/dev/null
				i=$j
			done
			gzip ${f}.1
		fi
	done
        cd -
}

compress_area()
{
	for d in `find $1 -type d -print`; do
                echo d: $d pwd: `pwd`
		compress_dir $d $2
	done
        unit=${3:-day}
        case $unit in
		day) 
			find $1 -type f -mtime $2 -delete
		     	;;
		hour) 
			find $1 -type f -mmin $(($2 * 60)) -delete
			;;
		*)	echo unknown time unit $3
	esac
}

cd $1
compress_area month 30 
compress_area week 7 
compress_area day 24 hour
