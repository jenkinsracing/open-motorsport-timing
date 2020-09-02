import csv
import io
from datetime import datetime

from werkzeug.datastructures import FileStorage

from app.models import DeviceItem, IOItem


class Importer(object):
    """Base importer object; must be subclassed and configured to import the require data"""
    def __init__(self):
        self.file = None
        self.items = []

    def read_data(self, file):
        self.file = file

        if isinstance(self.file, FileStorage):
            data = io.StringIO(file.stream.read().decode("UTF8", errors='ignore'), newline=None)
            self._read_csv(data)

        else:
            with open(self.file, 'r') as data:
                self._read_csv(data)

    def _read_csv(self, data):
        reader = csv.DictReader(data, dialect='excel')

        for row in reader:
            self.items.append(row)
            # print(row)

    def check_format(self):
        raise NotImplementedError

    def write_sql(self, db, project_id):
        # TODO this should delete all items from the project before importing; or compare and update only?
        raise NotImplementedError


class IOsImporter(Importer):
    def __init__(self):
        self.tcase = False
        super().__init__()

    def convert_testcase(self, tcase_name, username):
        self.tcase = True
        adapter = []

        for item in self.items:
            # print(item)
            d = {}
            d['Device'] = item['Device']
            d['Alias'], d['Description'] = self._tc_get_alias(item['Description'])
            d['Address'] = item['Address']
            d['Process'] = None
            d['Location'] = None
            d['Panel'] = None
            d['UserStamp'] = self._tc_convert_username(tcase_name, username, item)
            d['Tstamp'] = self._tc_convert_tstamp(item)
            d['Status'] = self._tc_convert_status(item)

            # print(d)
            adapter.append(d)

        self.items = adapter

    @staticmethod
    def _tc_get_alias(desc):
        if desc == '':
            return None, None
        if desc is None:
            return None, None
        i = desc.rfind(':')
        s1 = desc[:i]
        s2 = desc[i:].lstrip(':')
        return s1, s2

    @staticmethod
    def _tc_convert_username(tcase_name, username, item):
        if item['User'] == tcase_name:
            return username
        return None

    @staticmethod
    def _tc_convert_tstamp(item):
        if item['Time'] == '':
            return None

        # add leading 0
        if item['Time'].find(':', 0, 2) != -1:
            item['Time'] = '0' + item['Time']

        # print(item['Date'] + ' ' + item['Time'])
        tc_datetime = datetime.strptime(item['Date'] + ' ' + item['Time'], "%m/%d/%y %I:%M:%S %p")  # date time format from test case
        return tc_datetime

    @staticmethod
    def _tc_convert_status(item):
        tx = item['Status']

        if tx == 'DN':
            ntx = 'Done'
        elif tx == 'WT':
            ntx = 'Repeat'
        elif tx == 'RT':
            ntx = 'Repeat'
        elif tx == 'DI':
            ntx = 'Removed'
        elif tx == 'NS':
            ntx = 'Untested'
        elif tx == 'NW':
            ntx = 'Untested'
        else:
            ntx = None

        return ntx

    def check_format(self):
        # TODO make this more robust, should check all fields
        REQUIRED_FIELDS = ['Address']
        for k, v in self.items[0].items():
            if k == 'Address':
                return True
        return False

    def write_sql(self, db, project_id):
        # TODO check db for highest sort number and initialize from there
        sort = 1
        for d in self.items:
            # write to database
            if self.tcase:
                db.session.add(IOItem(project_id=project_id, sort=sort, **{k.lower(): v for k, v in d.items()}))
            else:
                db.session.add(IOItem(project_id=project_id, sort=sort, **{k.lower(): v for k, v in d.items()}))
            sort += 1
        db.session.commit()


class DevicesImporter(Importer):
    def __init__(self):
        self.tcase = False
        super().__init__()

    def check_format(self):
        # TODO make this more robust, should check all fields
        REQUIRED_FIELDS = ['Address']
        # FIXME check_format not implemented for device importer!
        return True

    def write_sql(self, db, project_id):
        # TODO check db for highest sort number and initialize from there
        sort = 1
        for d in self.items:
            # write to database
            db.session.add(DeviceItem(project_id=project_id, sort=sort, **{k.lower(): v for k, v in d.items()}))
            sort += 1
        db.session.commit()


if __name__ == "__main__":
    mystr1 = '=A-2025-MXZ01-T1_O_Start: Powerflex 525 Start'
    mystr2 = '=A-2054-QXV04:O1: MOZL Turbolizer water stop '

    test1 = mystr1.rfind(':')
    test2 = mystr2.rfind(':')
    test99 = 5
