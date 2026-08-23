#!/bin/sh
# Emit one line per agent when its process rotates onto code newer than $FIXTS.
cd "/Users/spiderishi/Coding/GLEE Competition" || exit 1
FIXTS="$1"
DONE=""
while true; do
  ALL=1
  for slot in hardliner randomized; do
    case " $DONE " in *" $slot "*) continue ;; esac
    ALL=0
    PID=$(pgrep -f "log-dir logs/$slot" | head -1)
    if [ -n "$PID" ]; then
      ST=$(ps -o lstart= -p "$PID" | xargs -I{} date -j -f "%a %b %d %T %Y" "{}" "+%s" 2>/dev/null)
      if [ -n "$ST" ] && [ "$ST" -gt "$FIXTS" ]; then
        echo "ROTATED: $slot pid $PID started $(date -u -r "$ST" +%H:%M:%SZ) -- now running the fixed code, safe to re-enable FP"
        DONE="$DONE $slot"
      fi
    fi
  done
  [ "$ALL" = "1" ] && exit 0
  sleep 30
done
