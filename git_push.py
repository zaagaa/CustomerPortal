import datetime
import os
import django
import socket

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CustomerPortal.settings")
django.setup()


import subprocess
from datetime import datetime

def run_git_command(cmd_list):
    result = subprocess.run(cmd_list, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
    else:
        print(f"✅ Success:\n{result.stdout}")

# Format current datetime in desired format: DD/MM/YYYY HH.MM AM/PM
now = datetime.now()
formatted_time = now.strftime("updated@%d/%m/%Y %I.%M %p")

# Run Git commands
run_git_command(['git', 'add', '.'])
run_git_command(['git', 'commit', '-m', formatted_time])
run_git_command(['git', 'push', 'origin', 'main'])