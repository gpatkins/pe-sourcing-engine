#!/bin/bash
echo "--- 🛑 Restarting App Container (Kills Zombies) ---"
sudo docker compose restart app

echo "\n--- 🧹 Vacuuming Database ---"
sudo docker compose exec db psql -U pe_sourcer -d pe_sourcing_db -c "VACUUM FULL;"

echo "\n--- 📉 Dropping System Cache ---"
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

echo "\n--- ✅ Done! Current Memory Usage: ---"
free -h
