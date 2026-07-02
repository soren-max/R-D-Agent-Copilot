# Deployment Guide

## Port Already In Use

When a service fails to start with `port already in use`, the usual cause is that an old process is still binding the same port or the deployment script started duplicate instances.

Recommended checks:

- Confirm the configured HTTP port in the service config.
- Use local host inspection to find the process that owns the port.
- Stop the old process before restarting the service.
- Check whether the deployment pipeline retried after a partial startup.

Risk note: do not kill unrelated system processes. Confirm the process name, working directory, and owner before stopping it.

## Failed Health Check After Deploy

If deployment succeeds but the health check fails, compare the runtime environment variables, listen port, dependency endpoints, and readiness timeout with the previous stable release.
