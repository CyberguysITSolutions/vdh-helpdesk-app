-- Migration 001: Add workflow columns for admin highlight and approval features
-- This migration is OPTIONAL and should be run if the columns do not already exist.
-- If your database already has these columns, you can skip this migration.

-- Add first_response_at to Tickets table to track when admin first views a ticket
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Tickets' 
    AND COLUMN_NAME = 'first_response_at'
)
BEGIN
    ALTER TABLE dbo.Tickets ADD first_response_at DATETIME NULL;
    PRINT 'Added first_response_at column to dbo.Tickets';
END
ELSE
BEGIN
    PRINT 'Column first_response_at already exists in dbo.Tickets';
END
GO

-- Add approved_by to Procurement_Requests to track who approved
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Procurement_Requests' 
    AND COLUMN_NAME = 'approved_by'
)
BEGIN
    ALTER TABLE dbo.Procurement_Requests ADD approved_by NVARCHAR(100) NULL;
    PRINT 'Added approved_by column to dbo.Procurement_Requests';
END
ELSE
BEGIN
    PRINT 'Column approved_by already exists in dbo.Procurement_Requests';
END
GO

-- Add approved_at to Procurement_Requests to track when approved
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Procurement_Requests' 
    AND COLUMN_NAME = 'approved_at'
)
BEGIN
    ALTER TABLE dbo.Procurement_Requests ADD approved_at DATETIME NULL;
    PRINT 'Added approved_at column to dbo.Procurement_Requests';
END
ELSE
BEGIN
    PRINT 'Column approved_at already exists in dbo.Procurement_Requests';
END
GO

-- Add approved_by to Vehicle_Trips for tracking vehicle request approvals
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Vehicle_Trips' 
    AND COLUMN_NAME = 'approved_by'
)
BEGIN
    ALTER TABLE dbo.Vehicle_Trips ADD approved_by NVARCHAR(100) NULL;
    PRINT 'Added approved_by column to dbo.Vehicle_Trips';
END
ELSE
BEGIN
    PRINT 'Column approved_by already exists in dbo.Vehicle_Trips';
END
GO

-- Add approved_at to Vehicle_Trips
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Vehicle_Trips' 
    AND COLUMN_NAME = 'approved_at'
)
BEGIN
    ALTER TABLE dbo.Vehicle_Trips ADD approved_at DATETIME NULL;
    PRINT 'Added approved_at column to dbo.Vehicle_Trips';
END
ELSE
BEGIN
    PRINT 'Column approved_at already exists in dbo.Vehicle_Trips';
END
GO

-- Add denial_reason to Vehicle_Trips for tracking denied requests
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'Vehicle_Trips' 
    AND COLUMN_NAME = 'denial_reason'
)
BEGIN
    ALTER TABLE dbo.Vehicle_Trips ADD denial_reason NVARCHAR(500) NULL;
    PRINT 'Added denial_reason column to dbo.Vehicle_Trips';
END
ELSE
BEGIN
    PRINT 'Column denial_reason already exists in dbo.Vehicle_Trips';
END
GO

PRINT 'Migration 001 completed successfully';
