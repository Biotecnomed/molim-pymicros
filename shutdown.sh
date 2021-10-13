#!/bin/bash

echo "Killing MOLIM-PYMICROS on port $1..."
kill -HUP `cat /tmp/uswgipid_$1.pid`
echo "DONE"