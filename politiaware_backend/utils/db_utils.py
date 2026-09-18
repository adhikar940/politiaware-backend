import psycopg2
import pandas as pd
import psycopg2
import os
from psycopg2.extras import execute_values
import csv
from io import StringIO
from dotenv import load_dotenv
ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(dotenv_path=ENV_FILE,override=True)  

class PostgresCSVHandler:
    def __init__(self):
        """
        Initialize the PostgresCSVHandler with PostgreSQL connection details.
        """
        self.conn_params = {
            "dbname": os.getenv('POSTGRES_DB'),
            "user": os.getenv('POSTGRES_USER'),
            "password": os.getenv('POSTGRES_PASSWORD'),
            "host": os.getenv('POSTGRES_HOST', 'db'),
            "port": os.getenv('POSTGRES_PORT', '5432')
        }

    def download_to_file(self, table_name, file_name, file_type='csv', columns=None):
        """
        Download data from a PostgreSQL table and save it as a CSV or XLSX file.
        """
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                col_clause = ', '.join(columns) if columns else '*'
                df = pd.read_sql(f"SELECT {col_clause} FROM {table_name}", conn)

            if file_type.lower() == 'xlsx':
                df.to_excel(file_name, index=False)
            else:
                df.to_csv(file_name, index=False)

            print(f"Data downloaded from '{table_name}' to '{file_name}'")

        except Exception as e:
            print(f"Download failed: {e}")

    def upload_from_file(self, file_name, table_name, columns=None):
        """
        Upload data from a CSV or XLSX file to a PostgreSQL table.

        Args:
            file_name (str): File path to CSV or XLSX.
            table_name (str): Target table.
            columns (list[str], optional): List of column names to insert into. If not given, uses DataFrame headers.
        """
        try:
            ext = os.path.splitext(file_name)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(file_name)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_name)
            else:
                raise ValueError("Only CSV or Excel files are supported")

            if columns is None:
                columns = df.columns.tolist()

            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        values = tuple(row[col] for col in columns)
                        placeholders = ', '.join(['%s'] * len(columns))
                        col_names = ', '.join([f'"{col}"' for col in columns])
                        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                        #col_names = ', '.join(columns)
                        #query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                        cur.execute(query, values)
                conn.commit()

            print(f"Data uploaded from '{file_name}' to table '{table_name}'")

        except Exception as e:
            print(f"Upload failed: {e}")
    

    def upload_from_file1(self, file_name, table_name, columns=None):
        """
        Upload data from a CSV or XLSX file to a PostgreSQL table using COPY for efficiency.

        Args:
            file_name (str): File path to CSV or XLSX.
            table_name (str): Target table.
            columns (list[str], optional): List of column names to insert into. If not given, uses DataFrame headers.
        """
        try:
            # Validate file extension
            ext = os.path.splitext(file_name)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(file_name, keep_default_na=False)  # Prevent converting empty strings to NaN
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_name, keep_default_na=False)
            else:
                raise ValueError("Only CSV or Excel files are supported")

            # Use DataFrame headers if columns not specified
            if columns is None:
                columns = df.columns.tolist()

            # Validate columns against table schema
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    # Get table columns
                    cur.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                    """, (table_name,))
                    table_columns = [row[0] for row in cur.fetchall()]
                    
                    if not all(col in table_columns for col in columns):
                        missing_cols = [col for col in columns if col not in table_columns]
                        raise ValueError(f"Columns {missing_cols} not found in table {table_name}")

                    # Prepare CSV data for COPY
                    csv_buffer = df.to_csv(index=False, header=False, quoting=csv.QUOTE_MINIMAL)
                    
                    # Use COPY for bulk insert
                    copy_sql = f"""
                        COPY {table_name} ({', '.join([f'"{col}"' for col in columns])})
                        FROM STDIN WITH (FORMAT csv, DELIMITER ',', HEADER FALSE, QUOTE '"', ESCAPE '''')
                    """
                    cur.copy_expert(copy_sql, StringIO(csv_buffer))
                    conn.commit()

            print(f"Data uploaded from '{file_name}' to table '{table_name}' successfully")

        except Exception as e:
            print(f"Upload failed: {e}")
            raise


if __name__ == "__main__":

    handler = PostgresCSVHandler()
    
    # handler.download_to_file(
    #     table_name="cm_cm",
    #     file_name="cm_export.xlsx",
    #     file_type="xlsx",
    #     columns=["id", "name", "rulingstate_id","party_id"]
    # )
    handler.download_to_file(
        table_name="loksabha_loksabha_constituency",
        file_name="loksabha_constituency.xlsx",
        file_type="xlsx"
    )
    # handler.download_to_file(
    #     table_name="area_pop_state",
    #     file_name="state.xlsx",
    #     file_type="xlsx"
    # )
    
    # # Download example (to CSV)
    # handler.download_to_file(
    #     table_name="cm_cm",
    #     file_name="cm_export.csv",
    #     file_type="csv",
    #     columns=["id", "name", "salary"]
    # )
    
    # # Upload example (from XLSX)
    # handler.upload_from_file(
    #     file_name="new_employees.xlsx",
    #     table_name="employees",
    #     columns=["id", "name", "salary"]
    # ) 
    # handler.upload_from_file1(
    #     file_name="loksabhamps (6).csv",
    #     table_name="loksabha_loksabhamp"
    # ) 
