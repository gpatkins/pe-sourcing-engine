#!/bin/bash
# DealGenome System Cleanup Script
# Called by admin dashboard cleanup endpoint

echo "--- 📉 Dropping System Cache ---"
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

echo "--- 💾 Current Memory Usage ---"
free -h

echo "--- ✅ Cleanup Complete ---"
