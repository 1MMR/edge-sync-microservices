import os
import time
import subprocess
import socket
import random
import sys
from datetime import datetime

RETRY_INTERVAL = int(os.getenv('SYNC_RETRY_SECONDS', '30'))
MAX_RETRIES = int(os.getenv('SYNC_MAX_RETRIES', '12'))
BACKOFF_FACTOR = float(os.getenv('SYNC_BACKOFF_FACTOR', '1.5'))

def check_internet(host="1.1.1.1", port=53, timeout=3):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except OSError:
        return False

def run(cmd, cwd=None, check=False, capture_output=False):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=capture_output, text=True)

def ensure_git_repo(path):
    if not os.path.exists(os.path.join(path, '.git')):
        run(['git', 'init'], cwd=path)

def has_changes(path):
    res = run(['git', 'status', '--porcelain'], cwd=path, capture_output=True)
    return bool(res.stdout.strip())

def safe_commit(path, message):
    run(['git', 'add', '--all'], cwd=path)
    if not has_changes(path):
        print('No changes to commit. Skipping commit.')
        return False
    run(['git', 'commit', '-m', message], cwd=path)
    return True

def ensure_remote(path, repo_url):
    res = run(['git', 'remote', 'get-url', 'origin'], cwd=path, capture_output=True)
    if res.returncode != 0 or (repo_url and repo_url not in res.stdout):
        run(['git', 'remote', 'remove', 'origin'], cwd=path)
        run(['git', 'remote', 'add', 'origin', repo_url], cwd=path)

def get_current_branch(path):
    res = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path, capture_output=True)
    if res.returncode == 0:
        return res.stdout.strip()
    return 'main'

def push_changes(path, branch='main', repo_url=None, use_http=False, token=None):
    ensure_remote(path, repo_url)
    current = get_current_branch(path)
    if current != branch:
        run(['git', 'checkout', '-B', branch], cwd=path)
    push_cmd = ['git', 'push', '-u', 'origin', branch]
    if use_http and token and repo_url:
        http_url = repo_url
        if repo_url.startswith('https://'):
            http_url = repo_url.replace('https://', f'https://{token}@')
            ensure_remote(path, http_url)
    res = run(push_cmd, cwd=path)
    return res.returncode == 0

def main():
    print('Sync Agent initialized. Monitoring connectivity...')
    data_dir = '/app/data'
    os.makedirs(data_dir, exist_ok=True)
    repo_ssh = os.getenv('GITHUB_REPO')
    repo_http = os.getenv('GITHUB_REPO_HTTP')
    token = os.getenv('GITHUB_TOKEN')
    use_http = bool(repo_http and token)
    target_repo = repo_http if use_http else repo_ssh

    attempt = 0
    while True:
        online = check_internet()
        report_path = os.path.join(data_dir, 'execution_report.json')

        if online and os.path.exists(report_path):
            print(f"Internet detected at {datetime.utcnow().isoformat()}! Preparing to push results to Git...")
            try:
                ensure_git_repo(data_dir)
                run(['git', 'config', 'user.name', 'Edge Bot'], cwd=data_dir)
                run(['git', 'config', 'user.email', 'bot@edge.local'], cwd=data_dir)

                committed = safe_commit(data_dir, 'Auto-sync: Offline workload completed successfully')
                if not committed:
                    print('Nothing new to push; finishing.')
                    break

                if not target_repo:
                    print('No target repo configured (GITHUB_REPO or GITHUB_REPO_HTTP + GITHUB_TOKEN). Cannot push.')
                    break

                pushed = push_changes(data_dir, branch='main', repo_url=target_repo, use_http=use_http, token=token)
                if pushed:
                    print('Successfully pushed to remote! Exiting sync loop.')
                    break
                else:
                    print('Push failed; will retry with backoff.')

            except Exception as e:
                print('Sync error:', e)

        attempt += 1
        if attempt > MAX_RETRIES:
            print('Exceeded max retries, exiting with failure.')
            sys.exit(2)

        interval = RETRY_INTERVAL * (BACKOFF_FACTOR ** (attempt - 1))
        jitter = interval * 0.1
        sleep_time = max(1, interval + random.uniform(-jitter, jitter))
        print(f'Offline or no report ready. Retrying in {int(sleep_time)} seconds... (attempt {attempt}/{MAX_RETRIES})')
        time.sleep(sleep_time)

if __name__ == '__main__':
    main()
