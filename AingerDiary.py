from kivy.app import App
from kivy.clock import Clock
# from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
# from kivy.uix.widget import Widget
# from kivy.garden.graph import Graph, MeshLinePlot
# from datetime import date
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from functools import partial
import sqlite3
import os

__author__ = "Unencrypted"


class ScreenTemplate(Screen):
    next_screen = ObjectProperty(None, allownone=True)
    prev_screen = ObjectProperty(None, allownone=True)

    def next(self):
        self.manager.switch_to(self.next_screen, direction="left")

    def prev(self):
        self.manager.switch_to(self.prev_screen, direction="right")

    @staticmethod
    def show_popup(*args):
        content = BoxLayout(orientation='vertical')
        things = dict()
        for text in args:
            things[text] = Label(text=text)
            content.add_widget(things[text])
        popup = Popup(title='Ошибка', content=content, size_hint=(0, 0), size=(400, 400))
        button = Button(text='Закрыть', size_hint=(None, 0.2), pos_hint={'center_x': 0.5})
        button.bind(on_press=popup.dismiss)
        content.add_widget(button)
        popup.open()


class MainScreen(ScreenTemplate):
    def go_try(self):
        self.switch("ask_date", "left")

    def go_show(self):
        self.switch("show", "left")


class ShowScreen(ScreenTemplate):
    pass


class TechniqueScreen(ScreenTemplate):
    def __init__(self, **kwargs):
        self.stack_usage = [False, False]
        self.stack = []
        super(TechniqueScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        self.ids["ask_dream"].check_box.bind(active=self.dream_changed)
        self.ids["ask_straight"].bind(is_checked=partial(self.changed, 0))
        self.ids["ask_lucid"].bind(is_checked=partial(self.changed, 1))
        self.ids["ask_indirect"].bind(is_checked=partial(self.changed, 1))

    def on_enter(self, *args):
        if not self.stack:
            self.stack = [self.manager.custom_screens["straight"],
                          self.manager.custom_screens["lucid"]]

    def dream_changed(self, widget, is_disabled):
        if is_disabled:
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = False
        else:
            self.ids["ask_lucid"].is_checked = self.ids["ask_indirect"].is_checked = False
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = True

    def changed(self, number, *args):
        if args[1]:
            self.stack_usage[number] = True
        else:
            self.stack_usage[number] = False
        for i in range(0, number + 1):
            if self.stack_usage[i]:
                self.next_screen = self.stack[i]
                break
            self.next_screen = None
        if number:
            self.manager.set_lucid(self.ids["ask_lucid"].is_checked)
            self.manager.set_indirect(self.ids["ask_indirect"].is_checked)

    def collect_data(self):
        return_dict = dict()
        return_dict["straight"] = self.ids["ask_straight"].is_checked
        return_dict["lucid"] = self.ids["ask_dream"].is_checked
        return_dict["indirect"] = self.ids["ask_indirect"].is_checked
        return return_dict


class AskDateScreen(ScreenTemplate):
    pick = ObjectProperty(None)


class StraightScreen(ScreenTemplate):
    def __init__(self, *args, **kwargs):
        super(StraightScreen, self).__init__(**kwargs)
        self.ids["straight_success"].bind(is_checked=self.change_straight_success_count_disabled)

    def change_straight_success_count_disabled(self, widget, value):
        self.ids["straight_success_count"].disabled = not value

    def next(self):
        technique_set = self.ids["cycle"].active \
                        or self.ids["alternation"].active \
                        or self.ids["one_technique"].active
        num_success_set = self.ids["straight_success"].is_checked \
                          and self.ids["straight_success_count"].text_input.text \
                          or not self.ids["straight_success"].is_checked
        if technique_set and num_success_set:
            self.calculate_next_screens()
            self.manager.switch_to(self.next_screen, direction="left")
            return
        content = []
        if not technique_set:
            content.append("Укажите тип используемых прямых техник")
        if not num_success_set:
            content.append("Укажите количество выходов")
        self.show_popup(*content)

    def on_leave(self, *args):
        if self.manager is not None:
            pass

    def collect_data(self):
        return_dict = dict()
        if self.ids["cycle"].active:
            return_dict["type"] = "cycle"
        elif self.ids["alternation"].active:
            return_dict["type"] = "alt"
        else:
            return_dict["type"] = "one"
        if self.ids["straight_success"].is_checked:
            return_dict["success"] = True
            return_dict["number"] = int(self.ids["straight_success_count"].text_input.text)
        else:
            return_dict["success"] = False
        return return_dict

    def calculate_next_screens(self):
        number_of_straight_exits = self.ids["straight_success_count"].text_input.text
        if number_of_straight_exits:
            number = int(number_of_straight_exits)
            last_screen = None
            for i in range(0, number):
                new_screen = ExitScreen(name="straight"+str(i))
                if last_screen is None:
                    self.next_screen = new_screen
                    last_screen = new_screen
                    new_screen.prev_screen = self
                else:
                    new_screen.prev_screen = last_screen
                    last_screen.next_screen = new_screen
                    last_screen = new_screen
            next_screen = self.manager.get_next_screen("straight")
            next_screen.prev_screen = last_screen
            last_screen.next_screen = next_screen
        else:
            next_screen = self.manager.get_next_screen("straight")
            self.next_screen = next_screen


class LucidScreen(ScreenTemplate):

    def next(self):
        quality_set = self.ids["dream_quality"].text_input.text
        lucid_number = self.ids["number_of_lucid_dreams"].text_input.text
        is_lucid_disabled = self.ids["number_of_lucid_dreams"].disabled
        indirect_number = self.ids["number_of_indirect_tries"].text_input.text
        is_indirect_disabled = self.ids["number_of_indirect_tries"].disabled
        if quality_set \
                and (is_lucid_disabled or (lucid_number and not is_lucid_disabled)) \
                and (is_indirect_disabled or (indirect_number and not is_indirect_disabled)):
                self.create_indirect_screens()
                self.next()
                return
        content = []
        if not quality_set:
            content.append('Укажите качество сна')
        if not lucid_number and not is_lucid_disabled:
            content.append('Укажите количество осознаний во сне')
        if not indirect_number and not is_indirect_disabled:
            content.append('Укажите количество непрямых попыток')
        self.show_popup(*content)

    def switch_lucid(self, on_off):
        self.ids["number_of_lucid_dreams"].disabled = not on_off

    def switch_indirect(self, on_off):
        self.ids["number_of_indirect_tries"].disabled = not on_off

    def collect_data(self):
        return_dict = dict()
        return_dict["quality"] = self.ids["dream_quality"].text_input.text
        if self.ids["number_of_lucid_dreams"].text_input.text:
            return_dict["lucid_number"] = int(self.ids["number_of_lucid_dreams"].text_input.text)
        if self.ids["number_of_indirect_tries"].text_input.text:
            return_dict["indirect_number"] = int(self.ids["number_of_indirect_tries"].text_input.text)
        return return_dict

    def create_indirect_screens(self):
        text_number_of_wakes = self.ids["number_of_lucid_dreams"].text_input.text
        if text_number_of_wakes:
            number_of_wakes = int(text_number_of_wakes)
            last_screen = None
            for i in range(0, number_of_wakes):
                new_screen = IndirectScreen(name="indirect"+str(i))
                if last_screen is None:
                    self.next_screen = new_screen
                    last_screen = new_screen
                    new_screen.prev_screen = self
                else:
                    new_screen.prev_screen = last_screen
                    last_screen.next_screen = new_screen
                    last_screen = new_screen
            next_screen = self.manager.get_next_screen("lucid")
            next_screen.prev_screen = last_screen
            last_screen.next_screen = next_screen
        else:
            self.next_screen = self.manager.get_next_screen("lucid")


class IndirectScreen(ScreenTemplate):

    def next(self):
        brightness = self.ids["brightness"].text_input.text
        cycles_text = self.ids["number_of_cycles"].text_input.text
        num_cycles = cycles_text or cycles_text == "0"
        if brightness and num_cycles:
            self.manager.indirect_next()
            return
        content = []
        if not brightness:
            content.append('Укажите яркость пробуждения')
        if not num_cycles:
            content.append('Укажите количество циклов техник')
        self.show_popup(*content)

    def collect_data(self):
        return_dict = dict()
        return_dict.brightness = int(self.ids["brightness"].text_input.text)
        return_dict.move = self.ids["was_moving"].is_checked
        return_dict.division = self.ids["try_division"].is_checked
        if return_dict.division:
            return_dict.success_division = self.ids["success_division"].is_checked
            if return_dict.success_division:
                return return_dict
        return_dict.num_cycles = int(self.ids["number_of_cycles"].text_input.text)
        return_dict.tech_exit = self.ids["technique_exit"].is_checked
        if return_dict.tech_exit:
            return return_dict
        return_dict.undesired_asleep = self.ids["undesired_asleep"].is_checked
        if not return_dict.undesired_asleep:
            return_dict.desired_asleep = self.ids["desired_asleep"].is_checked
        return return_dict


class ExitScreen(ScreenTemplate):
    pass


class EndScreen(ScreenTemplate):
    pass


class AskWidget(BoxLayout):
    label = ObjectProperty(None)
    label_text = StringProperty()
    check_box = ObjectProperty(None)
    is_checked = BooleanProperty()

    def __init__(self, **kwargs):
        super(AskWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0.01)

    def after_init(self, *args):
        self.check_box.bind(active=self.on_checkbox_active)
        self.is_checked = False
        self.ids["label"].text = self.label_text

    def on_checkbox_active(self, *args):
        if self.check_box.active:
            self.is_checked = True
        else:
            self.is_checked = False


class AskTextWidget(BoxLayout):
    label_text = StringProperty()
    text_input = ObjectProperty()

    def __init__(self, **kwargs):
        super(AskTextWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        self.ids["label"].text = self.label_text

    def return_text(self):
        return self.ids["text_input"].text


class AskNumWidget(AskTextWidget):
    minimum = NumericProperty(0)
    maximum = NumericProperty(0)

    def __init__(self, **kwargs):
        super(AskNumWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        super(AskNumWidget, self).after_init(*args)
        self.ids["text_input"].bind(text=self.check)

    def check(self, *args):
        buffer = ""
        for character in self.ids["text_input"].text:
            if character.isdigit():
                buffer += character
        if buffer:
            if int(buffer) < self.minimum:
                buffer = str(self.minimum)
            if self.maximum and int(buffer) > self.maximum:
                buffer = str(self.maximum)
            buffer = str(int(buffer))
        self.ids["text_input"].text = buffer


class WindowManager(ScreenManager):
    connection = None
    num_wakes = 0
    custom_screens = {}
    straight_present = False
    dream_present = False
    lucid_present = False
    indirect_present = False

    def __init__(self):
        super(WindowManager, self).__init__()
        base_path = os.getcwd() + os.sep + "AingerDiary.db"
        self.connection = sqlite3.connect(base_path)

    def set_lucid(self, is_enabled):
        self.custom_screens["lucid"].ids["number_of_lucid_dreams"].disabled = not is_enabled

    def set_indirect(self, is_enabled):
        self.custom_screens["lucid"].ids["number_of_indirect_tries"].disabled = not is_enabled

    def switch_show(self):
        self.switch_to(self.custom_screens["show"], direction="left")

    def switch_date(self):
        self.switch_to(self.custom_screens["ask_date"], direction="left")

    def get_next_screen(self, screen_name):
        data = self.custom_screens["technique"].collect_data()
        if screen_name == "straight":
            if data["lucid"] or data["indirect"]:
                return self.custom_screens["lucid"]
            else:
                return self.custom_screens["last"]
        if screen_name == "lucid":
            lucid_data = self.custom_screens["lucid"].collect_data()
            if "indirect_number" in lucid_data:
                screen = self.custom_screens["lucid"].create_indirect_screens()
                return screen
            else:
                return self.custom_screens["last"]


class AingerDiaryApp(App):
    def __init__(self, **kwargs):
        super(AingerDiaryApp, self).__init__(**kwargs)
        self.sm = WindowManager()

    def build(self):
        self.sm.custom_screens["main_menu"] = (MainScreen(name="main_menu"))
        self.sm.custom_screens["show"] = (ShowScreen(name="show",
                                                     prev_screen=self.sm.custom_screens["main_menu"]))
        self.sm.custom_screens["ask_date"] = (AskDateScreen(name="ask_date",
                                                            prev_screen=self.sm.custom_screens["main_menu"]))
        self.sm.custom_screens["technique"] = (TechniqueScreen(name="technique",
                                                               prev_screen=self.sm.custom_screens["ask_date"]))
        self.sm.custom_screens["ask_date"].next_screen = self.sm.custom_screens["technique"]
        self.sm.custom_screens["straight"] = (StraightScreen(name="straight",
                                                             prev_screen=self.sm.custom_screens["technique"]))
        self.sm.custom_screens["lucid"] = (LucidScreen(name="lucid",
                                                       prev_screen=self.sm.custom_screens["technique"]))
        self.sm.custom_screens["indirect"] = (IndirectScreen(name="indirect",
                                                             prev_screen=self.sm.custom_screens["technique"]))
        self.sm.custom_screens["last"] = (EndScreen(name="last"))
        self.sm.switch_to(self.sm.custom_screens["main_menu"])
        return self.sm


if __name__ == '__main__':
    AingerDiaryApp().run()
