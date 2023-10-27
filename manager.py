import datetime
from sqlite3 import connect
import os
from typing import List, Tuple, Literal, Union


def dict_factory(cursor, row):
    """
    Фабрика для того, чтобы получать из БД строки в формате dict
    Например:
        {
            'column_name1': 'value1',
            'column_name2': 'value2',
            ...
        }
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DbManager:
    """
    Класс для взаимодействия с БД
    (не предназначен для наследования).
    """
    NAME_APP = 'FilePlanner'
    DB_NAME = 'storage.db'

    def __init__(self):
        self.desktop, self.home = self.get_desktop()
        self.app_path = self.get_app_path(self.home)
        self.con, self.db_path = self.__get_db(self.app_path, factory='dict')
        self.sys_files = self.get_files_from_desktop(self.desktop)
        self.db_files = self.__get_files_from_db()
        self.__update_files(*self.__file_comparator())

    @classmethod
    def get_app_path(cls, home):
        """
        :param home: Путь к каталогу пользователя (~)
        :return: Путь к папке с файлами, необходимыми для работы приложения

        Метод для получения/создания пути хранения файлов для работы прирложения (БД).
        """
        app_path = os.path.join(home, cls.NAME_APP)
        if not os.path.exists(app_path):
            os.mkdir(app_path)
        return app_path

    @staticmethod
    def get_desktop() -> Tuple[str, str]:
        """
        :return: (desktop, home)

        Метод для получения пути к рабочему столу - desktop,
        пути к каталогу пользователя (~) - home.
        Если приложение не поддерживается, программа завершится с ошибкой "Unknown system"
        (просто закроется при сборке без консоли).
        """
        if os.name == 'nt':
            home = os.path.join(os.environ['USERPROFILE'])
            desktop = os.path.join(home, 'Desktop')
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Рабочий стол')
        elif os.name == 'posix':
            home = os.path.join(os.path.expanduser('~'))
            desktop = os.path.join(home, 'Desktop')
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Рабочий стол')
        else:
            exit("Unknown system")
        return desktop, home

    @staticmethod
    def get_files_from_desktop(desktop, pass_lnk=True) -> List:
        """
        :param desktop: Путь к рабочему столу
        :param pass_lnk: Флаг для пропуска ярлыков на рабочем столе (по умолчанию True)
        :return: Список файлов

        Метод для получения списка файлов с рабочего стола.
        """
        files = []
        for fname in os.listdir(desktop):
            fpath = os.path.join(desktop, fname)
            if fname and os.path.isfile(fpath) and not (fname.startswith('.') or fname.startswith('~')):
                files.append((fname, fpath))

        files = list(filter(lambda x: not (pass_lnk and x[1].endswith('.lnk')) and not x[1].endswith('.ini'), files))
        return files

    def __get_db(self, app_path, factory: Literal['dict', 'tuple'] = 'tuple'):
        """
        :param app_path: Путь к рабочему каталогу приложения (БД)
        :param factory: Выбор фабрики ('dict' или 'tuple')
        :return: Список файлов

        Метод для инициализации подключения к БД (создается новый файл, если не существует).
        Используется в инициализаторе класса.
        """
        db_path = os.path.join(app_path, self.DB_NAME)
        if not os.path.exists(db_path):
            con = connect(db_path)
            with con:
                cur = con.cursor()
                cur.execute("create table files "
                            "(id_file integer constraint files_pk primary key autoincrement, "
                            "name TEXT not null, "
                            "path TEXT not null)")

                cur.execute("create table file_date "
                            "( id integer constraint files_pk primary key autoincrement, "
                            "id_file integer not null, "
                            "fix_date  text  not null, "
                            "priority  integer default 1 not null)")
        else:
            con = connect(db_path)
        if factory == 'dict':
            con.row_factory = dict_factory
        return con, db_path

    def __get_files_from_db(self) -> List:
        """
        :return: Список файлов из БД в зависимости от фабрики ('tuple' или 'dict'), задаваемой через метод
            __get_db(*args)

        Метод для получения списка файлов из БД,
        требует предварительного запуска метода __get_db(*args) - для инициализации подключения.
        Используется в инициализаторе класса.
        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("select id_file, name, path from files")
            return cur.fetchall()

    def __file_comparator(self) -> Tuple[List, List]:
        """
        :return: Кортеж из двух списков:
            1. Список новых файлов на рабочем столе в формате List[Tuple('name', '\path\to\file'), ...];
            2. Список файлов, подлежащих удалению из БД в формате List['id_file', 'id_file', ...];

        Метод для получения двух списков: новых файлов на рабочем столе и подлежащих удалению из БД файлов,
        требует предварительного запуска метода __get_db(*args) с параметром factory='dict' для инициализации
        подключения self.con, get_files_from_desktop(self.desktop) для инициализации списка файлов self.sys_files и
        __get_files_from_db() для инициализации списка файлов в БД self.db_files. Используется в инициализаторе класса.
        """

        if not self.con.row_factory:
            raise RuntimeError("Need dict factory")
        removed_files = []
        new_files = []
        compare_list = list(map(lambda x: (x['name'], x['path']), self.db_files))
        for dictionary in self.db_files:
            if (dictionary['name'], dictionary['path']) not in self.sys_files:
                removed_files.append(str(dictionary['id_file']))
        for tuple_ in self.sys_files:
            if (tuple_[0], tuple_[1]) not in compare_list:
                new_files.append((str(tuple_[0]), str(tuple_[1])))
        return new_files, removed_files

    def __update_files(self, add: List, remove: List) -> None:
        """
        :param add: Список файлов для добавления в БД в формате List[Tuple['name', '\path\to\file'], ...]
        :param remove: Список идентификаторов файлов для удаления в БД в формате List[str(id_file), ...]
        :return: None

        Метод для актуализации файлов в БД: требует предварительного запуска метода __get_db(*args) для инициализации
        подключения self.con. Используется в инициализаторе класса.
        """
        with self.con:
            cur = self.con.cursor()
            if remove:
                cur.execute("delete from file_date where id_file in (%s)" % ("?," * len(remove))[:-1], remove)
                cur.execute("delete from files where id_file in (%s)" % ("?," * len(remove))[:-1], remove)
            for nf in add:
                cur.execute("insert into files (name, path) values (?, ?)", nf)

    def get_files_info(self) -> List:
        """
        :return: Список файлов из БД в зависимости от фабрики ('tuple' или 'dict'), задаваемой через метод
            __get_db(*args)

        Получение информации о файлах с количеством дней (записей): получение идентификатора файла, имя файла,
        путь к файлу, количество записей этого файла (сколько дней).
        """
        with self.con:
            cur = self.con.cursor()
            cur.execute('select id_file, name, path, count(id) as cnt '
                        'from files left join file_date using (id_file) group by 1, 2, 3 order by 2')
            return cur.fetchall()

    def get_days_info(self, month: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
                      year: Union[str, int], day: Union[str, int, None] = None, priority: bool = False):
        """
        :param month: Месяц (от 1 до 12)
        :param year: Год (yyyy)
        :param day: День (опционально) указывается для сужения выборки до одного дня
        :param priority: Поиск максимального приоритета, игнорируется, если день не указан
        :return: Список записей из БД в зависимости от фабрики ('tuple' или 'dict'), задаваемой через метод
            __get_db(*args), в случае, если priority=True возвращает кортеж/словарь в зависимости от фабрики,
            содержащий одно значение - максимальный приоритет в выбранный день (в случае словаря по ключу 'm_priority').
            Если день не указан, параметр priority будет проигнорирован.

        Получение информации о привязке файлах к дате: получение идентификатора файла, имени файла,
        пути к файлу, идентификатора записи о привязки файла и дня, даты привязки, приоритета привязки.
        При установлении параметров day и priority=True - получение максимального приоритета файла в данный день
        """
        month = f'{month:0>2}'
        year = str(year)
        with self.con:
            cur = self.con.cursor()
            if day:
                day = f'{day:0>2}'
                if priority:
                    cur.execute("select max(priority) as m_priority from file_date "
                                "where strftime('%Y-%m-%d', fix_date) = :date order by priority",
                                {'date': f'{year}-{month}-{day}'})
                    return cur.fetchone()
                cur.execute("select id_file, name, path, id as id_fix, fix_date, priority "
                            "from file_date left join files using (id_file) "
                            "where strftime('%Y-%m-%d', fix_date) = :date order by priority",
                            {'date': f'{year}-{month}-{day}'})
                return cur.fetchall()
            cur.execute("select id_file, name, path, id as id_fix, fix_date, priority "
                        "from file_date left join files using (id_file) "
                        "where strftime('%m.%Y', fix_date) = :date order by priority", {'date': month + '.' + year})
            return cur.fetchall()

    def add_new_days_file(self, date, file: object):
        """
        :param date: Дата (yyyy-mm-dd)
        :param file: Файл (Объект, имеющий атрибут id_file)

        :return: Список записей из БД по соответствующей дате в зависимости от фабрики ('tuple' или 'dict'),
            задаваемой через метод __get_db(*args).

        Добавление новой привязки файла и дня в БД. Предоставление нового списка привязок ко дню.
        """
        d = datetime.datetime.strptime(date, '%Y-%m-%d').timetuple()
        mon = d.tm_mon
        m_priority = self.get_days_info(mon, d.tm_year, d.tm_mday, priority=True)
        m_priority = m_priority['m_priority'] if m_priority and m_priority['m_priority'] else 0
        with self.con:
            cur = self.con.cursor()
            cur.execute('insert into file_date (id_file, fix_date, priority) values (?, ?, ?)',
                        (file.id_file, date, m_priority + 1))
        return self.get_days_info(mon, d.tm_year, d.tm_mday)

    def remove_day_file(self, date, id_file) -> None:
        """
        :param date: Дата (yyyy-mm-dd)
        :param id_file: Идентификатор файла

        :return: None

        Удаление привязки файла и дня в БД.
        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("delete from file_date "
                        "where strftime('%Y-%m-%d', fix_date) = :date and id_file = :id_file",
                        {'date': date, 'id_file': id_file})
