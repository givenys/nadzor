CREATE TABLE event_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    severity TEXT NOT NULL,
    auto_alert BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    face_embedding real[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE operators (
    id UUID PRIMARY KEY REFERENCES employees(id), 
    login TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    assigned_to UUID REFERENCES employees(id),
    rtsp_url TEXT,
    battery_level SMALLINT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    config JSONB
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    event_type_id UUID REFERENCES event_types(id),
    status TEXT NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    assigned_to UUID REFERENCES employees(id),
    description TEXT
);

CREATE TABLE detection_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id UUID REFERENCES devices(id),
    event_type_id UUID REFERENCES event_types(id),
    confidence FLOAT,
    bbox_w SMALLINT,
    bbox_h SMALLINT,
    bbox_x SMALLINT,
    bbox_y SMALLINT,
    gps_coords JSONB,
    tracking_id INTEGER,
    employee_id UUID REFERENCES employees(id),
    raw_data JSONB
);

CREATE INDEX idx_employees_full_name ON employees(full_name);
CREATE INDEX idx_operators_login ON operators(login);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_assigned_to ON incidents(assigned_to);
CREATE INDEX idx_devices_assigned_to ON devices(assigned_to);
CREATE INDEX idx_devices_is_active ON devices(is_active);
CREATE INDEX idx_detection_events_time ON detection_events(time);
CREATE INDEX idx_detection_events_device_id ON detection_events(device_id);
CREATE INDEX idx_detection_events_employee_id ON detection_events(employee_id);
CREATE INDEX idx_event_types_code ON event_types(code);