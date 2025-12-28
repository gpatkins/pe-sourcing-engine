#!/usr/bin/env python3
"""
PE Sourcing Engine v5.7 - Docker Management Console
Simplified management for v5.7 Docker deployment
"""

import os
import sys
import subprocess

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

DOCKER_COMPOSE_CMD = "docker compose -f docker-compose-v5.7.yml"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear_screen()
    print(f"{BOLD}*** PE Sourcing Engine v5.7 | Docker Management ***{RESET}")
    print(f"Working Directory: {os.getcwd()}")
    print("-" * 60)

def show_menu():
    print(f"\n{BOLD}Container Management:{RESET}")
    print(f" {BOLD}1){RESET} Start All Services")
    print(f" {BOLD}2){RESET} Stop All Services")
    print(f" {BOLD}3){RESET} Restart App Container")
    print(f" {BOLD}4){RESET} View Container Status")
    print(f" {BOLD}5){RESET} View Live Logs (App)")
    print(f"\n{BOLD}Database:{RESET}")
    print(f" {BOLD}6){RESET} Database Shell (psql)")
    print(f" {BOLD}7){RESET} Backup Database")
    print(f" {BOLD}8){RESET} View Database Stats")
    print(f"\n{BOLD}Maintenance:{RESET}")
    print(f" {BOLD}9){RESET} Container Cleanup")
    print(f" {BOLD}10){RESET} Rebuild Containers (No Cache)")
    print(f" {BOLD}11){RESET} View Documentation")
    print(f"\n{BOLD}0){RESET} Exit")
    print("-" * 60)

def run_command(cmd, ignore_error=False):
    """Execute shell command"""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_error:
            print(f"{RED}Error running command: {cmd}{RESET}")
        return False

def main():
    # Change to docker-v5.7 directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    while True:
        header()
        show_menu()
        choice = input(f"\n{YELLOW}Enter option: {RESET}").strip()

        if choice == "1":
            print(f"\n{BLUE}Starting all services...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} up -d")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "2":
            print(f"\n{BLUE}Stopping all services...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} down")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "3":
            print(f"\n{BLUE}Restarting app container...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} restart app")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "4":
            print(f"\n{BLUE}Container Status:{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} ps")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "5":
            print(f"\n{YELLOW}Press Ctrl+C to exit logs...{RESET}")
            try:
                run_command(f"{DOCKER_COMPOSE_CMD} logs -f --tail=50 app")
            except KeyboardInterrupt:
                pass
        
        elif choice == "6":
            print(f"\n{BLUE}Entering Database Shell (Type '\\q' to exit)...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} exec db psql -U pe_sourcer pe_sourcing_db")
        
        elif choice == "7":
            timestamp = subprocess.check_output("date +%Y%m%d_%H%M%S", shell=True).decode().strip()
            backup_file = f"backup_v57_{timestamp}.sql"
            print(f"\n{BLUE}Backing up database to {backup_file}...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} exec db pg_dump -U pe_sourcer pe_sourcing_db > {backup_file}")
            print(f"{GREEN}Backup saved: {backup_file}{RESET}")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "8":
            print(f"\n{BLUE}Database Statistics:{RESET}")
            run_command(f'{DOCKER_COMPOSE_CMD} exec db psql -U pe_sourcer pe_sourcing_db -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"')
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "9":
            print(f"\n{BLUE}Running container cleanup...{RESET}")
            run_command(f"{DOCKER_COMPOSE_CMD} exec app /app/docker-v5.7/docker-clean-v5.7.sh")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "10":
            confirm = input(f"\n{RED}Rebuild all containers? This will cause downtime. (y/n): {RESET}")
            if confirm.lower() == 'y':
                print(f"\n{BLUE}Stopping containers...{RESET}")
                run_command(f"{DOCKER_COMPOSE_CMD} down")
                print(f"\n{BLUE}Rebuilding (no cache)...{RESET}")
                run_command(f"{DOCKER_COMPOSE_CMD} build --no-cache")
                print(f"\n{BLUE}Starting services...{RESET}")
                run_command(f"{DOCKER_COMPOSE_CMD} up -d")
            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        
        elif choice == "11":
            run_command("less docker-README-v5.7.md")
        
        elif choice == "0":
            print(f"\n{GREEN}Goodbye!{RESET}")
            sys.exit(0)
        
        else:
            input(f"\n{RED}Invalid option. Press Enter to continue...{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Goodbye!{RESET}")
        sys.exit(0)
