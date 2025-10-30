-- Migration: create vehicles, trip_logs, service_logs, optional alerts
-- Adapt schema names/types as needed for your environment

-- Vehicles
CREATE TABLE dbo.vehicles (
  id INT IDENTITY(1,1) PRIMARY KEY,
  year INT NULL,
  make_model NVARCHAR(255) NOT NULL,
  vin NVARCHAR(64) NULL,
  license_plate NVARCHAR(32) NULL,
  photo_url NVARCHAR(1024) NULL,
  initial_mileage INT NOT NULL DEFAULT 0,
  current_mileage INT NOT NULL DEFAULT 0,
  last_service_mileage INT NULL,
  last_service_date DATETIME2 NULL,
  miles_until_service INT NOT NULL DEFAULT 4000,
  status NVARCHAR(32) NOT NULL DEFAULT 'motorpool',
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Trip logs (includes work_location)
CREATE TABLE dbo.trip_logs (
  id INT IDENTITY(1,1) PRIMARY KEY,
  vehicle_id INT NOT NULL REFERENCES dbo.vehicles(id) ON DELETE CASCADE,
  driver_user_id INT NULL,
  driver_name NVARCHAR(255) NULL,
  driver_phone NVARCHAR(64) NULL,
  driver_email NVARCHAR(255) NULL,
  work_location NVARCHAR(255) NULL,
  destination NVARCHAR(1024) NULL,
  purpose NVARCHAR(1024) NULL,
  departure_time DATETIME2 NOT NULL,
  return_time DATETIME2 NULL,
  mileage_departure INT NOT NULL,
  mileage_return INT NOT NULL,
  miles_used INT NULL,
  status NVARCHAR(32) NOT NULL DEFAULT 'active',
  notes NVARCHAR(MAX) NULL,
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Service logs
CREATE TABLE dbo.service_logs (
  id INT IDENTITY(1,1) PRIMARY KEY,
  vehicle_id INT NOT NULL REFERENCES dbo.vehicles(id) ON DELETE CASCADE,
  service_center NVARCHAR(255) NULL,
  date_of_service DATE NULL,
  work_performed NVARCHAR(MAX) NULL,
  dropped_off_by NVARCHAR(255) NULL,
  picked_up_by NVARCHAR(255) NULL,
  cost DECIMAL(12,2) NULL,
  receipt_file_url NVARCHAR(1024) NULL,
  notes NVARCHAR(MAX) NULL,
  created_by INT NULL,
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Optional alerts table for in-app alerts
CREATE TABLE dbo.fleet_alerts (
  id INT IDENTITY(1,1) PRIMARY KEY,
  vehicle_id INT NULL REFERENCES dbo.vehicles(id),
  alert_type NVARCHAR(64) NOT NULL,
  message NVARCHAR(1024) NOT NULL,
  created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  is_read BIT NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX IX_vehicles_status ON dbo.vehicles(status);
CREATE INDEX IX_vehicles_miles_until_service ON dbo.vehicles(miles_until_service);
CREATE INDEX IX_trip_logs_vehicle ON dbo.trip_logs(vehicle_id);
CREATE INDEX IX_trip_logs_location ON dbo.trip_logs(work_location);
CREATE INDEX IX_trip_logs_dates ON dbo.trip_logs(departure_time, return_time);
CREATE INDEX IX_service_logs_vehicle ON dbo.service_logs(vehicle_id);