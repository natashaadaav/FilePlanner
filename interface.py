import calendar
import os
import re
import sys
from datetime import date
from typing import Union

os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.resources import resource_add_path
from kivy.app import App
from kivy.core.window import Window
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


class FileWidget(Button):
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

    @classmethod
    def get_widget(cls, widget_gid):
        """returns widget if it is registered"""
        if widget_gid in cls.global_widgets:
            return cls.global_widgets[widget_gid]
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
            # print('not')
            # print(obj.files)
            manager = cls.get_widget('Manager')
            # current = manager.get_screen(manager.current)
            new_screen = manager.get_screen('DayScreen')
            new_screen.draw_screen(obj.files)
            manager.transition = SlideTransition()
            manager.transition.direction = 'right'
            manager.current = 'DayScreen'

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
        day_.files.append({
            'id_file': file_.id_file,
            'name': file_.name,
            'path': file_.path,
        })
        date_ = day_.day
        files_ = day_.files
        new_files = cls.db.add_new_days_file(day_.date, file_)
        day_.clear_widgets()
        day_.add_widget(DayLayout(date_, files_))

    @classmethod
    def deactivate_file(cls):
        if cls.selected_file:
            cls.selected_file.canvas.after.clear()
        cls.selected_file = None

    @staticmethod
    def next_month():
        if int(KivyWidgetInterface.current_month) == 12:
            KivyWidgetInterface.current_year = str(int(KivyWidgetInterface.current_year) + 1)
            KivyWidgetInterface.current_month = '01'
            KivyWidgetInterface.current_month_text = key_array[0]
        else:
            KivyWidgetInterface.current_month_text = key_array[int(KivyWidgetInterface.current_month)]
            KivyWidgetInterface.current_month = f'{int(KivyWidgetInterface.current_month) + 1:0>2}'

        calendar_obj = KivyWidgetInterface.get_widget('CalendarLayout')
        par = calendar_obj.parent
        calendar_obj.clear_widgets()
        calendar_obj.add_widget(MonthLayout())
        calendar_obj.add_widget(DayGrid())

    def previous_month(self):
        if int(KivyWidgetInterface.current_month) == 1:
            KivyWidgetInterface.current_year = str(int(KivyWidgetInterface.current_year) - 1)
            KivyWidgetInterface.current_month = '12'
            KivyWidgetInterface.current_month_text = key_array[11]
        else:
            KivyWidgetInterface.current_month = f'{int(KivyWidgetInterface.current_month) - 1:0>2}'
            KivyWidgetInterface.current_month_text = key_array[int(KivyWidgetInterface.current_month) - 1]

        calendar_obj = KivyWidgetInterface.get_widget('CalendarLayout')
        par = calendar_obj.parent
        calendar_obj.clear_widgets()
        calendar_obj.add_widget(MonthLayout())
        calendar_obj.add_widget(DayGrid())

    # @staticmethod
    # def clear_recursive(obj):
    #     children = obj.children
    #     if children:
    #         for ch in children:
    #             KivyWidgetInterface.clear_recursive(ch)
    #     else:
    #         obj.clear_widgets()
    #         obj.remove_widget(obj)


class ClosePopupButton(Button):
    ...


class RunPopupButton(Button):
    ...


class MainScreen(Screen, KivyWidgetInterface):
    ...


class DayScreen(Screen, KivyWidgetInterface):
    def draw_screen(self, files_list):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical')
        if not files_list:
            layout.add_widget(Label(text='nothing'))
        for file in files_list:
            layout_button = BoxLayout(orientation='horizontal')
            layout_button.add_widget(Label(text=file['name']))
            layout_button.add_widget(Button(text=f'delete {file["id_file"]}',
                                            on_release=lambda x: self.remove_file(file['id_file'])))
            layout.add_widget(layout_button)
        layout.add_widget(Button(text='cancel',
                                 on_release=self.to_main))
        self.add_widget(layout)

    def remove_file(self, file):
        pass

    def to_main(self, smth):
        manager = KivyWidgetInterface.get_widget('Manager')
        manager.transition = SlideTransition()
        manager.transition.direction = 'left'
        manager.current = 'MainScreen'


class ScrollV(KivyWidgetInterface, ScrollView):
    ...


class UserRelativeLayout(RelativeLayout):
    id = ObjectProperty('relative_layout')


class CalendarLayout(KivyWidgetInterface, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MainBox(BoxLayout):
    ...


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

        for i in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            self.add_widget(DayLabel(text=i))

        month = int(KivyWidgetInterface.current_month)
        year = int(KivyWidgetInterface.current_year)
        wd = date(year, month, 1).weekday()
        days = calendar.mdays[month]
        if calendar.isleap(year) and month == 2:
            days += 1
        for day in range(wd):
            self.add_widget(Label(text=''))
        for day in range(days):
            wd = (wd + 1) % 7
            days_files = [f['id_file'] for f in self.db.get_days_info(month, year, day + 1)]
            files_list = self.search_file_dict(days_files)
            self.add_widget(
                DayLayoutRel(day_=str(day + 1), date_=f'{year}-{month:0>2}-{(day + 1):0>2}', files_=files_list))


class ShadowBox(Widget):
    ...


class FileLayout(BoxLayout, KivyWidgetInterface):
    def __init__(self, **kwargs):
        super(FileLayout, self).__init__(**kwargs)
        for f in self.files:
            fw = FileWidget(f, length=self.get_fwidth(f['name']))
            self.add_widget(fw)


class Manager(ScreenManager, KivyWidgetInterface):
    main_screen = ObjectProperty(None)


class CalendarApp(KivyWidgetInterface, App):

    def build(self):
        # self.icon = icon
        Window.size = 700, 495
        # Window.size = 1000, 800
        sm = Manager()
        return sm


month_length = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    CalendarApp().run()
