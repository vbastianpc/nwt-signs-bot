from pathlib import Path
from subprocess import run

from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from sqlalchemy.exc import CompileError

from bot.database import PATH_DB


DBML_SCHEMA = Path(__file__).parent / 'schema.dbml'
DBSQL_SCHEMA = Path(__file__).parent / 'schema.sql'

engine = create_engine(rf'sqlite:///{PATH_DB}', echo=False)
metadata_obj = MetaData()
metadata_obj.reflect(bind=engine)

err = 0
with open(DBSQL_SCHEMA, 'w', encoding='utf-8') as f:
    for table in metadata_obj.sorted_tables:
        print(table, end=' ')
        try:
            f.write(CreateTable(table).compile(engine).string + ';')
        except CompileError:
            print('-'*30 + ' error')
            err += 1
        else:
            print()
print(f'\n{len(metadata_obj.tables) - err} of {len(metadata_obj.tables)} tables created')

run(['sql2dbml', DBSQL_SCHEMA, '-o', DBML_SCHEMA], check=True)
