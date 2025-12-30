#!/bin/bash
echo "\n--- 📉 Dropping System Cache ---"
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

echo "\n--- ✅ Done! Current Memory Usage: ---"
free -h
