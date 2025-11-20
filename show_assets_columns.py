import traceback
try:
    from fleet import fleet_db
    import pandas as pd
except Exception as e:
    print("ERROR importing fleet_db or pandas:", e)
    raise

def show_columns():
    q = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
      AND TABLE_NAME = 'Assets'
    ORDER BY ORDINAL_POSITION
    """
    try:
        conn = fleet_db.get_conn()
    except Exception as e:
        print("ERROR obtaining DB connection from fleet.fleet_db.get_conn():", e)
        return

    try:
        df = pd.read_sql(q, conn)
        print(df.to_string(index=False))
    except Exception as e:
        print("Query error:", e)
        print(traceback.format_exc())
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    show_columns()