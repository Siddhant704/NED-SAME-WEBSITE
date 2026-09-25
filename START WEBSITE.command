#!/bin/bash
cd "$(dirname "$0")"
pkill -f "server.py 8090" 2>/dev/null; pkill -f "http.server 8090" 2>/dev/null; sleep 1
python3 server.py 8090 &
sleep 2
open "http://localhost:8090/nedlloydgroup.com/"
echo "Nedlloyd website running at http://localhost:8090/nedlloydgroup.com/  (dashboard: /nedlloydgroup.com/dashboard.html)"
echo "Close this window when finished."
wait
