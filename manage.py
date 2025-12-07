#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import socket

# --- CONFIG ---
DOCKER_CMD = "sudo docker compose"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config", "generated_secrets.env")
README_FILE = os.path.join(APP_DIR, "README.md")

# --- COLORS ---
GREEN, RED, YELLOW, BLUE, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[0m"
BOLD = "\033[1m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_status():
    try:
        out = subprocess.check_output(f"{DOCKER_CMD} ps", shell=True).decode()
        if "Up" in out: return f"{GREEN}ONLINE{RESET}"
        return f"{RED}OFFLINE{RESET}"
    except: return f"{RED}ERROR{RESET}"

def run_cleanup():
    print(f"\n{YELLOW}--- 🧹 Starting System Cleanup ---{RESET}")
    
    print("1. Restarting App Container (Kills Zombies)...")
    subprocess.run(f"{DOCKER_CMD} restart app", shell=True)
    
    print("2. Vacuuming Database (Reclaims Disk Space)...")
    # We ignore errors here in case DB isn't running
    subprocess.run(f"{DOCKER_CMD} exec db psql -U pe_sourcer -d pe_sourcing_db -c 'VACUUM FULL;'", shell=True)
    
    print("3. Dropping System RAM Cache...")
    # Sync ensures data is written to disk before dropping cache
    subprocess.run("sync && echo 3 > /proc/sys/vm/drop_caches", shell=True)
    
    print(f"\n{GREEN}--- ✅ Cleanup Complete! Current Memory: ---{RESET}")
    subprocess.run("free -h", shell=True)
    input(f"\n{YELLOW}Press Enter to return...{RESET}")

def header():
    clear_screen()
    ip = get_ip()
    status = get_status()
    print(f"{BOLD}*** PE Sourcing Engine | Management Console ***{RESET}")
    print(f"Server IP:   {BLUE}{ip}{RESET}")
    print(f"Status:      {status}")
    print(f"Location:    {APP_DIR}")
    print("-" * 50)
    print(f"Dashboard:   http://{ip}:8000")
    print(f"Metabase:    http://{ip}:3000")
    print("-" * 50)

def show_menu():
    print(f" {BOLD}1){RESET} Check System Status")
    print(f" {BOLD}2){RESET} View Live Logs")
    print(f" {BOLD}3){RESET} Restart Engine")
    print(f" {BOLD}4){RESET} Stop Engine")
    print("-" * 20)
    print(f" {BOLD}5){RESET} Run Discovery")
    print(f" {BOLD}6){RESET} Run Enrichment")
    print(f" {BOLD}7){RESET} Run Scoring")
    print("-" * 20)
    print(f" {BOLD}8){RESET} Database Shell (SQL)")
    print(f" {BOLD}9){RESET} View Documentation (README)")
    print(f" {BOLD}10){RESET} Update API Keys / Config")
    print(f" {BOLD}11){RESET} System Cleanup / Memory Purge")  # <--- NEW OPTION
    print(f" {BOLD}0){RESET} Exit")
    print("-" * 50)

def main():
    while True:
        header()
        show_menu()
        choice = input("Enter option: ").strip()

        if choice == "1":
            subprocess.run(f"{DOCKER_CMD} ps", shell=True)
            input(f"\n{YELLOW}Press Enter...{RESET}")
        
        elif choice == "2":
            print(f"{YELLOW}Press Ctrl+C to exit logs...{RESET}")
            time.sleep(1)
            try:
                subprocess.run(f"{DOCKER_CMD} logs -f --tail=50 app", shell=True)
            except KeyboardInterrupt:
                pass
        
        elif choice == "3":
            print("Restarting...")
            subprocess.run(f"{DOCKER_CMD} restart", shell=True)
            time.sleep(2)
        
        elif choice == "4":
            print("Stopping...")
            subprocess.run(f"{DOCKER_CMD} stop", shell=True)
        
        elif choice == "5":
            subprocess.run(f"{DOCKER_CMD} exec app python3 -m etl.discover.google_places", shell=True)
            input(f"\n{YELLOW}Press Enter...{RESET}")

        elif choice == "6":
            subprocess.run(f"{DOCKER_CMD} exec app python3 enrich_companies.py", shell=True)
            input(f"\n{YELLOW}Press Enter...{RESET}")

        elif choice == "7":
            subprocess.run(f"{DOCKER_CMD} exec app python3 -m etl.score.calculate_scores", shell=True)
            input(f"\n{YELLOW}Press Enter...{RESET}")

        elif choice == "8":
            subprocess.run(f"{DOCKER_CMD} exec db psql -U pe_sourcer pe_sourcing_db", shell=True)

        elif choice == "9":
            subprocess.run(f"less {README_FILE}", shell=True)

        elif choice == "10":
            print(f"Opening config file: {CONFIG_FILE}")
            subprocess.run(f"nano {CONFIG_FILE}", shell=True)
            if input(f"{YELLOW}Restart engine to apply changes? (y/n): {RESET}").lower() == 'y':
                subprocess.run(f"{DOCKER_CMD} restart", shell=True)

        elif choice == "11":
            run_cleanup()

        elif choice == "0":
            sys.exit(0)

if __name__ == "__main__":
    try:
        # Check permissions (Needed for Docker and Cache drop)
        if os.geteuid() != 0:
            os.execvp("sudo", ["sudo", "python3"] + sys.argv)
        main()
    except KeyboardInterrupt:
        sys.exit(0)
