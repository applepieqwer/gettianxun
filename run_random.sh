dst_array=("nyca" "lond" "syda" "tyoa" "sins")
date_array=("2015-12-23" "2016-01-01" "2016-02-06" "2016-02-24")
while true
do
	r1=$((RANDOM%=5))
	r2=$((RANDOM%=4))
	python tianxun.py csha ${dst_array[$r1]} ${date_array[$r2]} $@
	rs=$((RANDOM%200+100))
	echo "bash sleeping $rs"
	sleep $rs
done
