-- Corrected migration: drop partial objects, add vehicle fields, create trips/receipts and procs
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

-- 0) Safety: drop previously created objects that may be partial from the failed run
IF OBJECT_ID('dbo.Vehicle_Trip_Receipts', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Vehicle_Trip_Receipts;
END
IF OBJECT_ID('dbo.Vehicle_Trips', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Vehicle_Trips;
END
IF OBJECT_ID('dbo.sp_ApproveVehicleTrip', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_ApproveVehicleTrip;
END
IF OBJECT_ID('dbo.sp_ReturnVehicleTrip', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_ReturnVehicleTrip;
END
GO

-- 1) Add vehicle-level fields if they do not already exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'initial_mileage')
BEGIN
    ALTER TABLE dbo.vehicles ADD initial_mileage INT NULL;
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'last_service_date')
BEGIN
    ALTER TABLE dbo.vehicles ADD last_service_date DATE NULL;
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'notes_log')
BEGIN
    ALTER TABLE dbo.vehicles ADD notes_log NVARCHAR(MAX) NULL;
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'picture_url')
BEGIN
    ALTER TABLE dbo.vehicles ADD picture_url NVARCHAR(400) NULL;
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'usage_count')
BEGIN
    ALTER TABLE dbo.vehicles ADD usage_count INT NOT NULL CONSTRAINT DF_vehicles_usage_count DEFAULT(0);
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'current_driver')
BEGIN
    ALTER TABLE dbo.vehicles ADD current_driver NVARCHAR(200) NULL;
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.vehicles') AND name = 'current_trip_id')
BEGIN
    ALTER TABLE dbo.vehicles ADD current_trip_id INT NULL;
END
GO

-- 2) Create Vehicle_Trips table (records procurements/uses/returns)
-- NOTE: this FK references dbo.vehicles.id (your PK)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.Vehicle_Trips') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.Vehicle_Trips
    (
        trip_id INT IDENTITY(1,1) PRIMARY KEY,
        vehicle_id INT NOT NULL,
        requester_first NVARCHAR(100) NOT NULL,
        requester_last NVARCHAR(100) NOT NULL,
        requester_email NVARCHAR(200) NOT NULL,
        requester_phone NVARCHAR(50) NULL,
        starting_mileage INT NULL,
        returning_mileage INT NULL,
        destination NVARCHAR(400) NULL,
        departure_time DATETIMEOFFSET NULL,
        return_time DATETIMEOFFSET NULL,
        status NVARCHAR(50) NOT NULL DEFAULT('Requested'), -- Requested, Approved, In Use, Returned, Cancelled
        created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
        approved_at DATETIME2 NULL,
        approved_by NVARCHAR(200) NULL,
        notification_unaccounted_sent BIT NOT NULL DEFAULT(0),
        notes NVARCHAR(MAX) NULL,
        CONSTRAINT FK_VehicleTrips_Vehicles FOREIGN KEY (vehicle_id) REFERENCES dbo.vehicles([id])
    );
    CREATE INDEX IX_VehicleTrips_VehicleId_Status ON dbo.Vehicle_Trips(vehicle_id, status);
    CREATE INDEX IX_VehicleTrips_Status_CreatedAt ON dbo.Vehicle_Trips(status, created_at);
END
GO

-- 3) Create Vehicle_Trip_Receipts table (store gas receipts or attachments)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.Vehicle_Trip_Receipts') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.Vehicle_Trip_Receipts
    (
        receipt_id INT IDENTITY(1,1) PRIMARY KEY,
        trip_id INT NOT NULL,
        filename NVARCHAR(260) NOT NULL,
        content_type NVARCHAR(100) NULL,
        file_data VARBINARY(MAX) NULL,
        uploaded_at DATETIME2 DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_TripReceipts_Trips FOREIGN KEY (trip_id) REFERENCES dbo.Vehicle_Trips(trip_id)
    );
    CREATE INDEX IX_TripReceipts_TripId ON dbo.Vehicle_Trip_Receipts(trip_id);
END
GO

-- 4) Stored proc to approve a trip and update vehicle state (use vehicles.id)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.sp_ApproveVehicleTrip') AND type IN (N'P'))
BEGIN
    EXEC('
    CREATE PROCEDURE dbo.sp_ApproveVehicleTrip
        @trip_id INT,
        @approver NVARCHAR(200)
    AS
    BEGIN
        SET NOCOUNT ON;
        BEGIN TRY
            BEGIN TRANSACTION;

            DECLARE @vehicle_id INT;

            SELECT @vehicle_id = vehicle_id
            FROM dbo.Vehicle_Trips
            WHERE trip_id = @trip_id;

            IF @vehicle_id IS NULL
            BEGIN
                RAISERROR(''Trip not found'', 16, 1);
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- Mark trip as Approved and set approved metadata
            UPDATE dbo.Vehicle_Trips
            SET status = ''Approved'', approved_at = SYSUTCDATETIME(), approved_by = @approver
            WHERE trip_id = @trip_id;

            -- Update vehicle to In Use, set current_trip_id and increment usage_count
            UPDATE dbo.vehicles
            SET [status] = ''In Use'',
                current_trip_id = @trip_id,
                usage_count = ISNULL(usage_count,0) + 1
            WHERE [id] = @vehicle_id;

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
            THROW;
        END CATCH
    END
    ')
END
GO

-- 5) Stored proc to mark a trip as Returned (set return info, clear vehicle state)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.sp_ReturnVehicleTrip') AND type IN (N'P'))
BEGIN
    EXEC('
    CREATE PROCEDURE dbo.sp_ReturnVehicleTrip
        @trip_id INT,
        @returning_mileage INT = NULL,
        @return_time DATETIMEOFFSET = NULL,
        @notes NVARCHAR(MAX) = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        BEGIN TRY
            BEGIN TRANSACTION;

            DECLARE @vehicle_id INT;

            SELECT @vehicle_id = vehicle_id FROM dbo.Vehicle_Trips WHERE trip_id = @trip_id;

            IF @vehicle_id IS NULL
            BEGIN
                RAISERROR(''Trip not found'', 16, 1);
                ROLLBACK TRANSACTION;
                RETURN;
            END

            UPDATE dbo.Vehicle_Trips
            SET returning_mileage = @returning_mileage,
                return_time = @return_time,
                status = ''Returned'',
                notes = COALESCE(notes,'''') + CHAR(13) + ''[Return at '' + CONVERT(NVARCHAR(30), ISNULL(@return_time,SYSUTCDATETIME())) + ''] '' + ISNULL(@notes,'''')
            WHERE trip_id = @trip_id;

            -- Clear vehicle current_trip_id and mark vehicle as Available
            UPDATE dbo.vehicles
            SET [status] = ''Available'',
                current_trip_id = NULL,
                current_driver = NULL
            WHERE [id] = @vehicle_id;

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
            THROW;
        END CATCH
    END
    ')
END
GO