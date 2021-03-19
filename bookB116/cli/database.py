from logging import getLogger
from contextlib import contextmanager
from sys import stdout
import csv

import click
from flask.cli import AppGroup

from bookB116 import db
from . import development


logger = getLogger(__name__)
cli = AppGroup('database', help='Operating database tables.')


def get_table(table_name):
    table = db.Model.metadata.tables.get(table_name)
    if table is None:
        raise click.BadParameter(
            f'Table not in {db.Model.metadata.tables.keys()}') from None
    return table


def ensure_development():
    if not development:
        raise click.Abort('Only do this in development mode.')


@contextmanager
def wrap_open(file_name, *args, **kwargs):
    if file_name == '-':
        yield stdout
    else:
        with open(file_name, *args, **kwargs) as f:
            yield f


def write_records(csv_file_name, records, columns):
    with wrap_open(csv_file_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(columns)
        for record in records:
            csv_writer.writerow(
                getattr(record, column)
                for column in columns
            )


@cli.command('list')
def list_tables():
    'List all table names.'

    click.echo(', '.join(db.Model.metadata.tables.keys()))


@cli.command('export')
@click.argument('table_name')
@click.argument('csv_file_name', type=click.Path(dir_okay=False))
def export(table_name, csv_file_name):
    '''
    Export all data in table to a csv file.

    To create a proper excel, open a blank worksheet in Excel,
    and import the data into it.
    '''

    table = get_table(table_name)
    write_records(
        csv_file_name,
        db.session.query(table).all(),
        table.columns.keys()
    )

    logger.info(f'Successfully exported table {table_name}')


@cli.command('init')
def creat_all():
    'Init all tables.'

    ensure_development()
    db.create_all()


@cli.command('delete')
@click.argument('table_name')
def delete(table_name):
    'Delete all data in a table'

    table = get_table(table_name)
    if not development:
        click.confirm('PRODUCTION mode!! Sure?', abort=True)
    click.confirm(f'DELETEING ALL DATA in {table_name}. Continue?', abort=True)
    db.session.query(table).delete(synchronize_session=False)
    db.session.commit()
    logger.warning(f'Deleted data in {table_name}')


@cli.command('drop')
@click.argument('table_name')
def drop(table_name):
    'Drop a table.'

    table = get_table(table_name)
    ensure_development()
    click.confirm(f'DROPING {table_name}. Continue?', abort=True)
    table.drop(db.engine)
    db.session.commit()
    logger.warning(f'Droped table {table_name}')


@cli.command('drop-all')
def drop_all():
    'Drop all tables. Cannot do this in production mode.'

    ensure_development()
    click.confirm('DROPING ALL TABLES!! Continue?', abort=True)
    db.drop_all()
    logger.warning('Droped all tables')
