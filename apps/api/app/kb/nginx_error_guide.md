# Nginx Error Guide

## 502 Bad Gateway

Nginx 502 often means the upstream service is unavailable, refused the connection, closed the connection early, or exceeded proxy timeout.

Recommended checks:

- Inspect upstream service health and listen port.
- Check `proxy_connect_timeout`, `proxy_read_timeout`, and upstream address.
- Compare Nginx config before and after deployment.
- Review application logs for startup failures.

## 413 Request Entity Too Large

For upload failures, check `client_max_body_size` and upstream request size limits.
