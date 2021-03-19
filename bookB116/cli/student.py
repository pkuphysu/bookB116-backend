from logging import getLogger

import click
from flask.cli import AppGroup

from bookB116.cli import dev_help_prod_error


logger = getLogger(__name__)
cli = AppGroup('student', help='Manage students.')


@cli.command('build')
@click.argument('path', nargs=-1,
                type=click.Path(exists=True, dir_okay=False))
@dev_help_prod_error
def build(path):
    '''
    Build student databse from csv file.

    通过一系列csv文件建立一个物院学生的数据库。
    数据库只要求存储姓名和学号之间对应关系，暂不涉及入学年份。

    The csv file should have a header
    '''
    from csv import reader

    from bookB116 import cryptor, db
    from bookB116.database import Student

    # There is no short hand method to IGNORE duplicate ids
    # session.add will raise an exception when duplicate
    # and session.merge will update the record,
    # which will erase other field and that's terrible.
    # And checking if the student exists every time is slow.
    # The code below creates an INSERT IGNORE sentence,
    # adding 2000 records in 3 sec in my VM
    inserter = Student.__table__.insert().prefix_with('IGNORE')

    for csv_file in path:
        with open(csv_file, encoding='utf-8-sig', newline='') as csvin:
            csvreader = reader(csvin)
            next(csvreader)  # Remove header line
            for row in csvreader:
                stu_id = row[0]
                if stu_id == '':
                    logger.info('Interesting empty lines by Excel')
                    continue
                db.session.execute(inserter.values(
                    stu_id=cryptor.hashit(stu_id)))
    db.session.commit()
    logger.info('Successfully built database '
                'from %s', ''.join(path))


@cli.command('add')
@click.argument('stu_ids', nargs=-1)
@dev_help_prod_error
def add(stu_ids):
    '''
    添加单个学生
    '''
    from bookB116 import cryptor, db
    from bookB116.database import Student

    inserter = Student.__table__.insert().prefix_with('IGNORE')

    for stu_id in stu_ids:
        db.session.execute(inserter.values(
            stu_id=cryptor.hashit(stu_id)))

    db.session.commit()
