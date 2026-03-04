#!/bin/bash
# Start VeriSight Demo Site

echo "Starting VeriSight Demo Site..."
cd demo
python -m http.server 8000
