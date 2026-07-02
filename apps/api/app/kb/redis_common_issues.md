# Redis Common Issues

## Connection Timeout

Redis timeout usually relates to network reachability, connection pool exhaustion, slow commands, or wrong password configuration.

Recommended checks:

- Verify host, port, password, and database index.
- Check client connection pool settings.
- Inspect Redis slowlog for blocking commands.
- Confirm whether deployment changed Redis endpoint configuration.

## Cache Miss Spike

A sudden cache miss spike can be caused by key prefix changes, TTL changes, cache flush, or incompatible serialization.
