# fix: resolve connection pool exhaustion under load

## Summary
- Replace per-request connections with SQLAlchemy connection pool
- Pool size: 20 connections, max overflow: 10
- Add pool health check and statistics endpoint

## Benchmarks
- Connections under load: 200 -> 20 (10x reduction)
- P99 latency: 450ms -> 120ms
- Max concurrent requests: 50 ->
