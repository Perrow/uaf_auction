inotifywait -e modify -m . |
while read -r directory events filename; do
  if [ "$filename" = "auktion.db3" ]; then
    cp auktion.db3 auktion_$(date +%Y-%m-%d_%k:%M:%S:%N).db3
  fi
done

# Needs inotify-tools, install with:
# sudo apt install inotify-tools 

# -e modify is the event type to watch for
# -m is monitoring mode
# . is directory to watch, ie current directory

# The output of inotifywait is directory event and filename so the outpus is piped to while read loop 
# if the modified file is the interesting one copy it to some place with date and time added to the filename so it will save copies of all changes
