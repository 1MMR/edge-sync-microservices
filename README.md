# Edge-Sync Microservices Platform with Autonomous Git-Reconciliation

Edge-Sync Microservices Platform with Autonomous Git-Reconciliation — air-gapped local microservices that auto-sync execution reports to GitHub when connectivity is restored.

## Quick Start

Prerequisites:
- Docker / Docker Compose (or Docker Desktop)
- Git (for the sync agent to push)

Clone the repository:

    git clone https://github.com/1MMR/edge-sync-microservices.git
    cd edge-sync-microservices

Build and run the stack:

    docker compose up --build

What happens:
- `workload-engine` runs an offline batch and writes `/app/data/execution_report.json` into the shared `./shared-data` volume.
- `sync-agent` watches for connectivity and, when online, commits and pushes the report to the `GITHUB_REPO` you configure.

Notes & recommended adjustments:
- SSH/known_hosts: mounting your host `~/.ssh` into the container as read-only prevents the container from writing `known_hosts` (host key verification). Either pre-populate `known_hosts` on the host, mount a writable ssh directory, or use HTTPS with a PAT for pushes.
- Configure the sync agent's target repo by setting the `GITHUB_REPO` environment variable in `docker-compose.yml` or by overriding it at runtime.

## Repository layout

- services/workload: Workload engine Dockerfile + app
- services/sentinel: Sentinel service Dockerfile
- services/sync-agent: Sync agent Dockerfile + sync script
- shared-data: Volume mounted between services for reports and artifacts
- docs/progress/kanban.md: One-week sprint tracker

