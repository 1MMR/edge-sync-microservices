import os
import time
import subprocess
import socket


def check_internet():
    try:
        # Check connection to Cloudflare DNS
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        return False

print("Sync Agent initialized. Monitoring connectivity...")

RETRY_INTERVAL = int(os.getenv('SYNC_RETRY_SECONDS', '30'))

while True:
    if check_internet() and os.path.exists("/app/data/execution_report.json"):
        print("Internet detected! Pushing results to GitHub...")
        try:
            os.chdir("/app/data")
            # Initialize micro-repo inside shared data to commit results
            subprocess.run(["git", "init"], check=False)
            subprocess.run(["git", "config", "user.name", "Edge Bot"], check=False)
            subprocess.run(["git", "config", "user.email", "bot@edge.local"], check=False)
            subprocess.run(["git", "add", "execution_report.json"], check=False)
            subprocess.run(["git", "commit", "-m", "Auto-sync: Offline workload completed successfully"], check=False)

            # Push to remote repository
            repo_url = os.getenv("GITHUB_REPO")
            if not repo_url:
                print("GITHUB_REPO not set; cannot push. Set the environment variable to your target repo.")
            else:
                subprocess.run(["git", "remote", "add", "origin", repo_url], check=False)
                result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=False)

                if result and result.returncode == 0:
                    print("Successfully alerted GitHub account! Exiting sync loop.")
                    break
                else:
                    print("Push failed or returned non-zero; will retry.")
        except Exception as e:
            print("Sync error:", e)

    print("Offline or no report ready. Retrying in {} seconds...".format(RETRY_INTERVAL))
    time.sleep(RETRY_INTERVAL)
