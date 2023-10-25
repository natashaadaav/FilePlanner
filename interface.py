import re
from typing import Union
from datetime import date
import calendar

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager, Screen
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


class FileWidget(Button):
    # id_file = NumericProperty() name, path
    def __init__(self, fconfiguration: dict, length: float, **kwargs):
        super(FileWidget, self).__init__(**kwargs)
        self.id_file = fconfiguration['id_file']
        self.name = fconfiguration['name']
        self.path = fconfiguration['path']
        self.text = self.name
        self.width = length


class DayLayout(Button, BoxLayout):
    day = StringProperty()
    files = ObjectProperty()

    def __init__(self, day_='', files_=None, **kwargs):
        super().__init__(**kwargs)
        if files_ is None:
            files_ = []
        self.day = day_
        self.files = files_


class DayLayoutRel(RelativeLayout):
    date = StringProperty()
    day = StringProperty()
    files = ObjectProperty()

    def __init__(self, day_='', date_='', files_=None, **kwargs):
        super().__init__(**kwargs)
        if files_ is None:
            files_ = []
        self.date = date_
        self.day = day_
        self.files = files_
        self.add_widget(DayLayout(day_=self.day, files_=self.files))


m_rgba = (.9, .9, .9, 1)
a_rgba = (.1, .1, .8, .4)
db_manager = DbManager()
db_files = db_manager.get_files_info()
# db_files = [FileWidget(f, length=0) for f in db_files]
# fw = FileWidget(f, length=self.get_fwidth(f['name']))

key_array = ('Январь', 'Февраль',
             'Март', 'Апрель', 'Май',
             'Июнь', 'Июль', 'Август',
             'Сентябрь', 'Октябрь', 'Ноябрь',
             'Декабрь')


class KivyWidgetInterface:
    ''' interface for  global widget access '''

    db = db_manager
    current_month = '10'  # todo инициализация now()
    current_year = '2023'  # todo инициализация now()
    current_month_text = key_array[10 - 1]
    files = db_files
    # files = [{'id_file': 2, 'name': '12.txt', 'path': 'desktop/12.txt'},
    #          {'id_file': 4, 'name': '14.txt', 'path': 'desktop/14.txt'},
    #          {'id_file': 4, 'name': '14 .txt', 'path': 'desktop/14.txt'},
    #          {'id_file': 4, 'name': '24.txt', 'path': 'desktop/14.txt'},
    #          {'id_file': 4, 'name': '24 .txt', 'path': 'desktop/14.txt'},
    #          {'id_file': 5, 'name': '15.txt', 'path': 'desktop/15.txt'},
    #          {'id_file': 6, 'name': '16.txt', 'path': 'desktop/16.txt'},
    #          {'id_file': 8, 'name': 'abobabobbababa.txt', 'path': 'desktop/abobabobbababa.txt'},
    #          {'id_file': 9, 'name': 'abobabo jkds sdfkj .dfg. drg bbababa.txt',
    #           'path': 'desktop/abobabo jkds sdfkj .dfg. drg bbababa.txt'},
    #          {'id_file': 7, 'name': '17.txt', 'path': 'desktop/17.txt'}]  # from db
    kf = 8.3
    standard_background_color = ObjectProperty()
    global_widgets = {}
    name_app = StringProperty("Calendar")
    file_widget_height = NumericProperty(30)
    file_panel_padding = NumericProperty(10)
    file_panel_height = NumericProperty(30 + 2 * 10)
    main_rgba = ObjectProperty(m_rgba)
    accent_rgba = ObjectProperty(a_rgba)

    selected_file = None

    @classmethod
    def get_fwidth(cls, text):
        bchar = len(list(filter(lambda x: not re.match(r'[;:,."\'!\s]', x), text)))
        schar = len(list(filter(lambda x: re.match(r'[;:,."\'!\s]', x), text)))
        return bchar * cls.kf + schar * cls.kf / 2

    @classmethod
    def get_sum_fwidth(cls):
        return sum(cls.get_fwidth(f['name']) for f in cls.files)

    def register_widget(self, widget_object):
        """registers widget only if it has unique gid"""
        if widget_object.gid not in self.global_widgets:
            self.global_widgets[widget_object.gid] = widget_object

    def get_widget(self, widget_gid):
        """returns widget if it is registered"""
        if widget_gid in self.global_widgets:
            return self.global_widgets[widget_gid]
        else:
            return None

    @staticmethod
    def add_canvas(self, dark=False, clear=False):
        color = (1, 0, 1, .5)
        if clear:
            self.canvas.after.clear()
            return 0
        with self.canvas.after:
            Color(*color)
            RoundedRectangle(pos=[self.pos[0] + self.padding[0], self.pos[1] + self.padding[3]],
                             size=[self.size[0] - self.padding[0] - self.padding[2],
                                   self.size[1] - self.padding[1] - self.padding[3]],
                             radius=[(10, 10), (10, 10), (10, 10), (10, 10)])

    @staticmethod
    def on_scroll_up(sv):
        if sv.scroll_x > 1.1 or sv.scroll_x < -0.1:
            pass
            # sv.update_pl()

    @classmethod
    def select_file(cls, obj: FileWidget):
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
        # print(cls.selected_file.text)

    @classmethod
    def search_file_dict(cls, id_file: Union[int, list]) -> list:
        if not id_file:
            return []
        if isinstance(id_file, list):
            result = []
            for f in cls.files:
                if f['id_file'] in id_file:
                    result.append(f)

            return result
        else:
            for f in cls.files:
                if f['id_file'] == id_file:
                    return [f]
        return []

    @classmethod
    def select_day(cls, obj: DayLayoutRel):
        if not cls.selected_file:
            print('not')
            print(obj.files)
            return None  # todo select other screen

        rule = cls.selected_file not in obj.files

        popup = ModalViewAdd()
        layout = PopupLayout()

        buttons_lay = ButtonLayout()
        buttons_lay.add_widget(ClosePopupButton(on_release=popup.dismiss))
        buttons_lay.add_widget(
            RunPopupButton(on_release=lambda x: cls.update_day(cls.selected_file, obj, popup))) if rule else None

        text = f'Файл\n{cls.selected_file.text}\nуже добавлен на {obj.date}' if not rule else \
            f'Вы действительно \nхотите добавить файл\n\n{cls.selected_file.text}\nна {obj.date}'

        layout.add_widget(PopupLabel(text=text))
        layout.add_widget(buttons_lay)
        popup.add_widget(layout)
        popup.open()

    @classmethod
    def update_day(cls, file_, day_: DayLayoutRel, dialog: Popup):
        dialog.dismiss()
        cls.deactivate_file()
        # self.id_file = fconfiguration['id_file']
        #         self.name = fconfiguration['name']
        #         self.path = fconfiguration['path']
        day_.files.append({
            'id_file': file_.id_file,
            'name': file_.name,
            'path': file_.path,
        })
        date_ = day_.day
        files_ = day_.files
        new_files = cls.db.add_new_days_file(day_.date, file_)
        # todo update interface
        for child in day_.children:
            cls.clear_recursive(child)
        day_.add_widget(DayLayout(date_, files_))

    # popup = PopupAdd(title='hello', content=Label(text='Hello world'),
    #                          size_hint=(None, None), size=(400, 400))
    #         popup.open()

    @classmethod
    def deactivate_file(cls):
        if cls.selected_file:
            cls.selected_file.canvas.after.clear()
        cls.selected_file = None

    def next_month(self):
        print('next')

    def previous_month(self):
        print('previous')

    @staticmethod
    def clear_recursive(obj):
        child = obj.children
        if child:
            for ch in child:
                KivyWidgetInterface.clear_recursive(ch)
        else:
            obj.clear_widgets()
            obj.remove_widget(obj)

    def update_widget(self, gid):
        widget = self.get_widget(gid)
        child = widget.children
        KivyWidgetInterface.clear_recursive(child)

    # def update_pl(self):
    #     sv = self.get_widget('ScrollV')
    #     pl = sv.children[0]
    #     pl.clear_widgets()
    #     pl.remove_widget(pl)
    # sv.clear_widgets()
    # sv.add_widget(ProductLayout())


class ClosePopupButton(Button):
    ...


class RunPopupButton(Button):
    ...


class MainScreen(Screen):
    ...


class DayScreen(Screen):
    ...
    # def __init__(self, **kwargs):
    #     super(MainScreen, self).__init__(**kwargs)


class ScrollV(KivyWidgetInterface, ScrollView):
    ...


class UserRelativeLayout(RelativeLayout):
    id = ObjectProperty('relative_layout')


class CalendarLayout(KivyWidgetInterface, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.add_widget(DayGrid())


class MonthLayout(BoxLayout):
    ...


class DayLabel(Label):
    ...


class PopupLabel(Label):
    ...


class ModalViewAdd(ModalView):
    ...


class PopupLayout(BoxLayout):
    ...


class ButtonLayout(BoxLayout):
    ...


class DayGrid(KivyWidgetInterface, GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # print(self.db.get_days_info(self.current_month, self.current_year))

        for i in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            self.add_widget(DayLabel(text=i))

        month = int(self.current_month)
        year = int(self.current_year)
        wd = date(year, month, 1).weekday()
        days = calendar.mdays[month]
        if calendar.isleap(year) and month == 2:
            days += 1
        for day in range(wd):
            self.add_widget(Label(text=''))
        for day in range(days):
            wd = (wd + 1) % 7
            # days_files = [f['id_file'] for f in self.db.get_files_info()]
            days_files = [f['id_file'] for f in self.db.get_days_info(month, year, day + 1)]
            files_list = self.search_file_dict(days_files)
            self.add_widget(DayLayoutRel(day_=str(day + 1), date_=f'{year}-{month:0>2}-{(day + 1):0>2}', files_=files_list))


class ShadowBox(Widget):
    ...


class FileLayout(BoxLayout, KivyWidgetInterface):
    def __init__(self, **kwargs):
        super(FileLayout, self).__init__(**kwargs)
        for f in self.files:
            fw = FileWidget(f, length=self.get_fwidth(f['name']))
            self.add_widget(fw)


class Manager(ScreenManager):
    # login_screen = ObjectProperty(None)
    main_screen = ObjectProperty(None)


class CalendarApp(KivyWidgetInterface, App):

    def build(self):
        # self.icon = icon
        Window.size = 700, 495
        # Window.size = 1000, 800
        sm = Manager()
        return sm


month_length = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


# def print_month(month, year):
#     if month < 1 or month > 12:
#         raise RuntimeError('uncorrected month')
#
#     wd = date(year, month, 1).weekday()
#     days = calendar.mdays[month]
#     if calendar.isleap(year) and month == 2:
#         days += 1
#
#     print(f"{month} {year}".center(20))
#     print("Пн Вт Ср Чт Пт Сб Вс")
#     print('   ' * wd, end='')
#     for day in range(days):
#         wd = (wd + 1) % 7
#         eow = " " if wd % 7 else "\n"
#         print(f"{day + 1:2}", end=eow)
#     print()


if __name__ == "__main__":
    # print_month(2, 2020)

    CalendarApp().run()
