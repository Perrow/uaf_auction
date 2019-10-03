inotifywait -e modify -m . |
while read -r directory events filename; do
  if [ "$filename" = "auktion.db3" ]; then
    cp auktion.db3 auktion_$(date +%Y-%m-%d_%k:%M:%S:%N).db3
  fi
done