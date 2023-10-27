import calendar
import datetime
import os
import re
import sys

from datetime import date
from typing import Union

# Запрет kivy вести журнал (необходимо выполнять до импорта kivy)
os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.config import Config
from kivy.resources import resource_add_path
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
# noinspection PyUnresolvedReferences
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
# noinspection PyUnresolvedReferences
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from manager import DbManager


class FileWidget(BoxLayout, Button):
    """Класс макета для установки параметров файла"""

    def __init__(self, fconfiguration: dict, **kwargs):
        super().__init__(**kwargs)
        self.id_file = fconfiguration['id_file']
        self.name = fconfiguration['name']
        self.path = fconfiguration['path']


class DayLayout(Button, BoxLayout):
    """Класс макета для дня календаря (основной макет)"""
    day = StringProperty()
    files = ObjectProperty()
    wd = NumericProperty()

    def __init__(self, day_='', files_=None, wd=0, **kwargs):
        super().__init__(**kwargs)
        if files_ is None:
            files_ = []
        self.day = day_
        self.files = files_
        self.wd = wd


class DayLayoutRel(RelativeLayout):
    """Класс макета для дня календаря (внешний макет, содержащий основной макет дня и тень)"""
    date = StringProperty()
    day = StringProperty()
    files = ObjectProperty()
    wd = NumericProperty()

    def __init__(self, day_='', date_='', files_=None, wd=0, **kwargs):
        super().__init__(**kwargs)
        if files_ is None:
            files_ = []
        self.date = date_
        self.day = day_
        self.files = files_
        self.wd = wd
        self.add_widget(DayLayout(day_=self.day, files_=self.files, wd=wd))


m_rgba = (.9, .9, .9, 1)
a_rgba = (.09, .15, .69, .8)
h_rgba = (1, .95, .95, 1)
db_manager = DbManager()
db_files = db_manager.get_files_info()

holidays = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (23, 2), (8, 3), (1, 5), (9, 5), (12, 6), (4, 11)]
key_array = ('Январь', 'Февраль',
             'Март', 'Апрель', 'Май',
             'Июнь', 'Июль', 'Август',
             'Сентябрь', 'Октябрь', 'Ноябрь',
             'Декабрь')


class KivyWidgetInterface:
    """
    Класс для глобального доступа к виджетам, которые его наследуют + некоторые глобальные методы и аттрибуты класса
    """

    db = db_manager
    current_month = f'{datetime.date.today().month:0>2}'
    current_year = str(datetime.date.today().year)
    current_month_text = key_array[datetime.date.today().month - 1]
    files = db_files
    kf = 8.3
    standard_background_color = ObjectProperty()
    global_widgets = {}
    name_app = StringProperty(db_manager.NAME_APP)
    file_widget_height = NumericProperty(35)
    file_panel_padding = NumericProperty(10)
    file_panel_height = NumericProperty(35 + 2 * 10)
    main_rgba = ObjectProperty(m_rgba)
    accent_rgba = ObjectProperty(a_rgba)
    hot_rgba = ObjectProperty(h_rgba)

    selected_file = None

    def register_widget(self, widget_object):
        """
        :param widget_object: экземпляр виджета

        Добавляет виджет в список для возможности последующего доступа к нему по свойству gid (должно быть уникальным)
        """
        if widget_object.gid not in self.global_widgets:
            self.global_widgets[widget_object.gid] = widget_object

    @classmethod
    def get_widget(cls, widget_gid):
        """
        :param widget_gid: gid виджета
        :return: экземпляр виджета

        Возращает виджет по свойству gid
        """
        if widget_gid in cls.global_widgets:
            return cls.global_widgets[widget_gid]
        else:
            return None

    @classmethod
    def select_file(cls, obj: FileWidget):
        """
        :param obj: экземпляр FileWidget

        Вызывается при нажатии на FileWidget (одна из кнопок с именем файла на верхней панели главного экрана).
        Устанавливает поданный obj файл выбранным и доступным на уровне приложения или удаляет из
        области видимости внутри приложения, если он был выбран ранее.
        """
        if cls.selected_file is obj:
            cls.deactivate_file()
            return None
        cls.deactivate_file()

        cls.selected_file = obj
        obj.canvas.after.clear()
        with obj.canvas.after:
            Color(*a_rgba)
            RoundedRectangle(pos=obj.pos,
                             size=obj.size,
                             radius=[(5, 5), (5, 5), (5, 5), (5, 5)])

    @classmethod
    def select_day(cls, obj: DayLayoutRel):
        """
        :param obj: экземпляр класса DayLayoutRel (DayLayout.parent)

        Вызывается при нажатии на DayLayout (одна из кнопок календаря - день).
        Если в области видимости внутри приложения есть файл (выбранный файл), то вызывается окно PopupLayout.
        Если в области видимости внутри приложения нет файла (файл не выбран), то происходит смена экрана на экран
        дня (DayScreen)
        """
        if not cls.selected_file:
            manager = cls.get_widget('Manager')
            new_screen = manager.get_screen('DayScreen')
            new_screen.draw_screen(obj.files, obj.date)
            manager.transition = SlideTransition()
            manager.transition.direction = 'right'
            manager.current = 'DayScreen'
            return None
        ids = [x['id_file'] for x in obj.files]
        rule = cls.selected_file.id_file not in ids

        popup = ModalViewAdd()
        layout = PopupLayout()

        buttons_lay = ButtonLayout()
        buttons_lay.add_widget(ClosePopupButton(on_release=popup.dismiss))
        buttons_lay.add_widget(
            RunPopupButton(on_release=lambda x: cls.update_day(cls.selected_file, obj, popup))) if rule else None

        text = f'\nФайл\n\n{cls.selected_file.name}\n\nуже добавлен на {obj.date}' if not rule else \
            f'\nВы действительно \nхотите добавить файл\n\n{cls.selected_file.name}\n\nна {obj.date}'

        layout.add_widget(PopupLabel(text=text))
        layout.add_widget(buttons_lay)
        popup.add_widget(layout)
        popup.open()

    @classmethod
    def update_day(cls, file_: FileWidget, day_: DayLayoutRel, dialog: Union[Popup, ModalView]):
        """
        :param file_: экземпляр класса FileWidget
        :param day_: экземпляр класса DayLayoutRel (DayLayout.parent)
        :param dialog: экземпляр класса ModalView|Popup

        Вызывается при нажатии на RunPopupButton (кнопка 'Сохранить' в всплывающем окне).
        Деактивирует выбранный файл из области видимости внутри приложения, добавляет новую привязку дня и файла,
        обновляет БД и интерфейс.
        """
        dialog.dismiss()
        cls.deactivate_file()
        day_.files.append({
            'id_file': file_.id_file,
            'name': file_.name,
            'path': file_.path,
        })
        date_ = day_.day
        files_ = day_.files
        wd = day_.wd
        new_files = cls.db.add_new_days_file(day_.date, file_)
        day_.clear_widgets()
        day_.add_widget(DayLayout(date_, files_, wd))

    @classmethod
    def deactivate_file(cls):
        """
        Удаляет файл из области видимости внутри приложения.
        """
        if cls.selected_file:
            cls.selected_file.canvas.after.clear()
        cls.selected_file = None

    @staticmethod
    def next_month():
        """
        Обновляет интерфейс в соответствии со следующим месяцем, вызывается при нажатии на правый треугольнк внутри
        макета MonthLayout
        """
        if int(KivyWidgetInterface.current_month) == 12:
            KivyWidgetInterface.current_year = str(int(KivyWidgetInterface.current_year) + 1)
            KivyWidgetInterface.current_month = '01'
            KivyWidgetInterface.current_month_text = key_array[0]
        else:
            KivyWidgetInterface.current_month_text = key_array[int(KivyWidgetInterface.current_month)]
            KivyWidgetInterface.current_month = f'{int(KivyWidgetInterface.current_month) + 1:0>2}'

        calendar_obj = KivyWidgetInterface.get_widget('CalendarLayout')
        calendar_obj.clear_widgets()
        calendar_obj.add_widget(MonthLayout())
        calendar_obj.add_widget(DayGrid())

    @staticmethod
    def previous_month():
        """
        Обновляет интерфейс в соответствии с предыдущим месяцем, вызывается при нажатии на левый треугольнк внутри
        макета MonthLayout
        """
        if int(KivyWidgetInterface.current_month) == 1:
            KivyWidgetInterface.current_year = str(int(KivyWidgetInterface.current_year) - 1)
            KivyWidgetInterface.current_month = '12'
            KivyWidgetInterface.current_month_text = key_array[11]
        else:
            KivyWidgetInterface.current_month = f'{int(KivyWidgetInterface.current_month) - 1:0>2}'
            KivyWidgetInterface.current_month_text = key_array[int(KivyWidgetInterface.current_month) - 1]

        calendar_obj = KivyWidgetInterface.get_widget('CalendarLayout')
        calendar_obj.clear_widgets()
        calendar_obj.add_widget(MonthLayout())
        calendar_obj.add_widget(DayGrid())


class MainScreen(Screen, KivyWidgetInterface):
    """Класс главного экрана, наследует KivyWidgetInterface для удобства использования свойств и методов"""


class FileLayout(BoxLayout, KivyWidgetInterface):
    """
    Класс макета для размещения виджетов файлов (FileWidget),
    наследует KivyWidgetInterface для удобства использования свойств и методов
    """

    def __init__(self, **kwargs):
        super(FileLayout, self).__init__(**kwargs)
        for f in self.files:
            name = f['name'] if len(f['name']) <= 29 else f['name'][:27] + '...'
            fw = FileWidget(f, text=name)
            self.add_widget(fw)


class ScrollV(KivyWidgetInterface, ScrollView):
    """
    Класс макета с прокруткой содержимого (панели файлов), наследует KivyWidgetInterface для удобства
    использования свойств и методов
    """


class UserRelativeLayout(RelativeLayout):
    """Класс макета выерхней панели основного экрана"""


class CalendarLayout(KivyWidgetInterface, BoxLayout):
    """Класс макета для календаря, наследует KivyWidgetInterface для удобства использования свойств и методов"""


class MainBox(BoxLayout):
    """Класс макета основного экрана"""


class MonthLayout(BoxLayout):
    """Класс макета для заголовков календаря (месяц, год, кнопки переключения месяца)"""


class DayGrid(KivyWidgetInterface, GridLayout):
    """Класс макета для дней календаря, наследует KivyWidgetInterface для удобства использования свойств и методов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for i in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            self.add_widget(DayLabel(text=i, bold=True))

        month = int(KivyWidgetInterface.current_month)
        year = int(KivyWidgetInterface.current_year)
        wd = date(year, month, 1).weekday()
        days = calendar.mdays[month]
        if calendar.isleap(year) and month == 2:
            days += 1
        for day in range(wd):
            self.add_widget(Label(text=''))
        for day in range(days):
            wds = 6 if (day + 1, month) in holidays else wd
            wd = (wd + 1) % 7
            # days_files = [f['id_file'] for f in self.db.get_days_info(month, year, day + 1)]
            files_list = self.db.get_days_info(month, year, day + 1)
            dlr = DayLayoutRel(day_=str(day + 1), date_=f'{year}-{month:0>2}-{(day + 1):0>2}', files_=files_list,
                               wd=wds)
            self.add_widget(dlr)


class DayLabel(Label):
    """Класс виджета, предназначенный для отображения надписи (день недели)"""


class ModalViewAdd(ModalView):
    """Класс виджета для отображения окна поверх всех элементов (модальное окно)"""


class PopupLayout(BoxLayout):
    """Класс макета модального окна"""


class ButtonLayout(BoxLayout):
    """Класс макета для кнопок модального окна"""


class PopupLabel(Label):
    """Класс виджета, предназначенный для отображения надписи (тело модального окна)"""


class ClosePopupButton(Button):
    """Класс кнопки модального окна (для закрытия модального окна), появляющегося при выборе файла и дня"""


class RunPopupButton(Button):
    """Класс кнопки модального окна (для обновления привязки дня и файла), появляющегося при выборе файла и дня"""


class DayScreen(Screen, KivyWidgetInterface):
    """
    Класс экрана для отображения связок файл-день,
    наследует KivyWidgetInterface для удобства использования свойств и методов
    """

    def draw_screen(self, files_list: list, file_date: str):
        """
        :param files_list: Список файлов для отображения и управления
        :param file_date: Дата для отображения и управления
        Собирает макет экрана для отображения связок файл-день и управления ими.
        """
        self.clear_widgets()
        layout = MainDeleteBox()
        ll = DeleteButtonCancelRel(size_hint_y=None, height=self.file_widget_height)
        ll.add_widget(DeleteButton(text=file_date, y=1))
        layout.add_widget(ll)
        scroll_area = DeleteScroll()

        layout_delete = DeleteLayout(orientation='vertical')
        if not files_list:
            layout_delete.add_widget(Label(text='Файлы не добавлены', color=(0, 0, 0, 1)))
        for file in files_list:
            layout_button = DeleteButtonRel(size_hint_y=None, height=self.file_widget_height)
            btn = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.file_widget_height)
            btn.add_widget(DeleteLabel(text=file['name']))
            btn_ = DeleteButton(text=f'Удалить', size_hint_x=None, width=80)
            btn_.id_file = file['id_file']
            btn_.date = file_date
            btn_.on_release = btn_.remove_file
            btn.add_widget(btn_)
            layout_button.add_widget(btn)
            layout_delete.add_widget(layout_button)
        layout.add_widget(scroll_area)
        scroll_area.add_widget(layout_delete)
        btn_cancel = DeleteButtonCancelRel(size_hint_y=None, height=self.file_widget_height)
        btn_cancel.add_widget(DeleteButton(text='Назад', size_hint_y=None, height=self.file_widget_height,
                                           on_release=self.to_main))
        layout.add_widget(btn_cancel)
        self.add_widget(layout)

    @staticmethod
    def to_main(*args, **kwargs):  # метод принимает объект, из которого она вызывалась (аргументы не удалять)
        """Переход на главный экран (MainScreen)"""
        manager = KivyWidgetInterface.get_widget('Manager')
        manager.transition = SlideTransition()
        manager.transition.direction = 'left'
        manager.current = 'MainScreen'


class MainDeleteBox(BoxLayout):
    """Класс макета для отображения связок файл-день"""


class DeleteScroll(ScrollView):
    """Класс макета с прокруткой содержимого (макета DeleteLayout с виджетами файлов в связках файл-день)"""


class DeleteLayout(BoxLayout):
    """Класс макета c виджетами файлов в связках файл-день"""


class DeleteButton(Button):
    """Класс кнопки для удаления связки файл-день"""
    id_file = NumericProperty()
    date = StringProperty()

    def remove_file(self):
        """Метод для удаления связки файл-день из БД и из интерфейса"""
        KivyWidgetInterface.db.remove_day_file(self.date, self.id_file)
        calendar_obj = KivyWidgetInterface.get_widget('CalendarLayout')
        calendar_obj.clear_widgets()
        calendar_obj.add_widget(MonthLayout())
        calendar_obj.add_widget(DayGrid())
        self.parent.parent.parent.remove_widget(self.parent.parent)


class DeleteButtonRel(RelativeLayout):
    """
    Класс макета для кнопки удаления связки файл-день (внешний макет, содержащий
    основной макет для управления связками файл-день и тень)
    """


class DeleteButtonCancelRel(DeleteButtonRel):
    """
    Класс макета для верхней и нижней панелей экрана для отображения связок файл-день - DayScreen
    (внешний макет, содержащий основной макет и тень)
    """


class DeleteLabel(Label):
    """Класс виджета, предназначенный для отображения надписи (имя файла)"""


class ShadowBox(Widget):
    """Класс виджета для добавления тени"""


class Manager(ScreenManager, KivyWidgetInterface):
    """Класс для управления экранами, наследует KivyWidgetInterface для удобства использования свойств и методов"""
    main_screen = ObjectProperty(None)


class CalendarApp(KivyWidgetInterface, App):
    """ Класс приложения, наследует KivyWidgetInterface для удобства использования свойств и методов """

    def build(self):
        self.title = self.name_app
        sm = Manager()
        return sm


month_length = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

if __name__ == "__main__":
    # Установка фиксированной ширины окна
    Config.set('graphics', 'width', '700')
    Config.set('graphics', 'height', '495')
    Config.set('graphics', 'resizable', '0')
    Config.write()
    if hasattr(sys, '_MEIPASS'):
        # Получение папки с временными файлами, необходимыми PyInstaller для создания одного файла *.exe
        resource_add_path(os.path.join(sys._MEIPASS))
    CalendarApp().run()
