# feat: implement OpenTelemetry tracing

## Summary
- Instrument HTTP client/server with OTEL
- Database query spans with timing
- OTLP exporter configuration
- Trace context propagation

## Test plan
- [x] Verify spans created for all HTTP calls
- [x] Test trace propagation across services
- [x] Validate OTLP export format
