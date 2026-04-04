-- Migration 002: Add audit log for data changes

CREATE TABLE health.audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id TEXT,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_table ON health.audit_log(table_name, changed_at);
CREATE INDEX idx_audit_log_record ON health.audit_log(table_name, record_id);

CREATE OR REPLACE FUNCTION health.audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO health.audit_log (table_name, operation, record_id, old_values, new_values, changed_by)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE TG_OP WHEN 'DELETE' THEN OLD::TEXT ELSE NEW::TEXT END,
        CASE TG_OP WHEN 'INSERT' THEN NULL ELSE row_to_json(OLD) END,
        CASE TG_OP WHEN 'DELETE' THEN NULL ELSE row_to_json(NEW) END,
        current_user
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER observations_audit
    AFTER INSERT OR UPDATE OR DELETE ON health.observations
    FOR EACH ROW EXECUTE FUNCTION health.audit_trigger();

CREATE TRIGGER alerts_audit
    AFTER INSERT OR UPDATE OR DELETE ON health.alerts
    FOR EACH ROW EXECUTE FUNCTION health.audit_trigger();
