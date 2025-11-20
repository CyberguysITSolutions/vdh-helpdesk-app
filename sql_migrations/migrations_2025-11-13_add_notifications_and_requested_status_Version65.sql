-- Add Notifications table (optional) and update vehicles status constraint to include 'Requested'
-- Run in a single execution in the SQL editor (execute the whole file). Test in staging first.

-- 1) Create Notifications table if missing
IF OBJECT_ID('dbo.Notifications', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Notifications (
        notification_id INT IDENTITY(1,1) PRIMARY KEY,
        notification_type NVARCHAR(100) NOT NULL, -- 'ticket','vehicle_request', etc.
        reference_id INT NULL,                     -- e.g., ticket_id or trip_id
        title NVARCHAR(250) NOT NULL,
        body NVARCHAR(MAX) NULL,
        recipients NVARCHAR(1000) NULL,            -- comma-separated emails
        is_read BIT DEFAULT 0,
        created_at DATETIME2 DEFAULT SYSUTCDATETIME()
    );

    CREATE INDEX IX_Notifications_IsRead_CreatedAt ON dbo.Notifications(is_read, created_at DESC);
END;
GO

-- 2) Update vehicles status constraint to include 'Requested'
-- Remove any existing status constraint for vehicles (if present)
DECLARE @existing_ck NVARCHAR(200);

SELECT @existing_ck = cc.name
FROM sys.check_constraints cc
JOIN sys.tables t ON cc.parent_object_id = t.object_id
WHERE t.name = 'vehicles' AND cc.definition LIKE '%status%';

IF @existing_ck IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.vehicles DROP CONSTRAINT ' + QUOTENAME(@existing_ck) + ';');
END;
GO

-- Add a new constraint (if vehicles table exists)
IF OBJECT_ID('dbo.vehicles', 'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.vehicles
    ADD CONSTRAINT CK_vehicles_status CHECK (status IN ('Available', 'Dispatched', 'Maintenance', 'Out Of Service', 'Requested'));
END;
GO

-- 3) Ensure notes_log column exists on vehicles (optional - only add if not present)
IF OBJECT_ID('dbo.vehicles', 'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.vehicles', 'notes_log') IS NULL
    BEGIN
        ALTER TABLE dbo.vehicles ADD notes_log NVARCHAR(MAX) NULL;
    END;
END;
GO

-- Verification queries (run separately if you like)
-- SELECT COUNT(*) AS notifications_count FROM dbo.Notifications;
-- SELECT name, definition FROM sys.check_constraints WHERE parent_object_id = OBJECT_ID('dbo.vehicles');
-- SELECT TOP 5 id, status, notes_log FROM dbo.vehicles;
GO