import sqlalchemy

class to_postgresql():
    def __init__(self, port=None, host=None, user=None, password=None, database=None, schema=None):
        self.schema=schema
        self.engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
                pool_pre_ping=True,pool_recycle=1800,connect_args={"connect_timeout": 30},
                executemany_mode="values_plus_batch",executemany_batch_page_size=500)

    def create_table(self, table_name=None, data=None):
        column_name = ', '.join(f'"{d}" DATE' if d == 'date' or d == 'Дата' else f'"{d}" TEXT' for d in data.columns.tolist())

        with self.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(f'CREATE SCHEMA IF NOT EXISTS {self.schema}')
            )
            connection.execute(
                sqlalchemy.text(
                    f'CREATE TABLE IF NOT EXISTS {self.schema}."{table_name}" ({column_name})'
                )
            )

    def sql_query(self, query=None):
        with self.engine.begin() as connection:
            connection.execute(sqlalchemy.text(query))

    def insert_into_table(self, table_name=None, data=None):
        data = data.copy()
        data = data.where(pd.notna(data), None)
        columns = data.columns.tolist()
        placeholders = [f"column_{index}" for index in range(len(columns))]
        columns_sql = ", ".join(f'"{c}"' for c in columns)
        placeholders_sql = ", ".join(f":{c}" for c in placeholders)

        insert_sql = sqlalchemy.text(
            f'INSERT INTO {self.schema}."{table_name}" ({columns_sql}) VALUES ({placeholders_sql})'
        )

        rows = [
            {placeholder: row[column] for placeholder, column in zip(placeholders, columns)}
            for row in data.to_dict(orient="records")
        ]

        with self.engine.begin() as connection:
            connection.execute(insert_sql, rows)
