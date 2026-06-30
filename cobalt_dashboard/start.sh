#!/bin/bash
cd /home/agent/data/sites/cobalt-dash
exec python3 app.py >> cobalt.log 2>&1
