for i in 1 2; do
  firefox &
  pid=$!
  sleep 15
  kill -9 $pid
done