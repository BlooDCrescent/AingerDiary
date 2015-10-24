from kivy.app import App
from kivy.clock import Clock
# from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import Calendar
# from kivy.uix.widget import Widget
from graph import Graph, MeshLinePlot
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

    def create_screens(self, screen_type, count):
        types = {"straight": ExitScreen, "lucid": ExitScreen, "indirect": IndirectScreen}
        type_names = {"straight": "Прямой выход", "lucid": "Осознание во сне", "indirect": ""}
        to_remove = []
        for screen in self.manager.custom_screens:
            if screen.startswith(screen_type) and not (screen == screen_type):
                to_remove.append(screen)
        for screen in to_remove:
            self.manager.custom_screens.pop(screen, None)
        return_screen = new_screen = types[screen_type](name=screen_type + "0", screen_type=type_names[screen_type])
        self.manager.custom_screens[new_screen.name] = new_screen
        new_screen.prev_screen = self
        last_screen = new_screen
        for i in range(0, count - 1):
            new_screen = types[screen_type](name=(screen_type + str(i + 1)), screen_type=type_names[screen_type])
            new_screen.prev_screen = last_screen
            last_screen.next_screen = new_screen
            last_screen = new_screen
            self.manager.custom_screens[new_screen.name] = new_screen
        last_screen.next_screen = None
        return return_screen, last_screen


class MainScreen(ScreenTemplate):
    def go_try(self):
        self.switch("ask_date", "left")

    def go_show(self):
        self.switch("show", "left")


class ShowScreen(ScreenTemplate):
    pass


class TechniqueScreen(ScreenTemplate):
    def __init__(self, **kwargs):
        self.stack_usage = [False, False, False, False, True]
        self.stack = []
        self.binding = False
        super(TechniqueScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        pass

    def dream_changed(self, widget, is_disabled):
        if is_disabled:
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = False
        else:
            self.ids["ask_lucid"].is_checked = self.ids["ask_indirect"].is_checked = False
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = True
        self.changed(1, None, is_disabled)

    def on_enter(self, *args):
        if not self.binding:
            self.ids["ask_dream"].bind(is_checked=self.dream_changed)
            self.ids["ask_straight"].bind(is_checked=partial(self.changed, 0))
            self.ids["ask_lucid"].bind(is_checked=partial(self.changed, 2))
            self.ids["ask_indirect"].bind(is_checked=partial(self.changed, 3))
            self.binding = True
        if not self.stack:
            self.stack = [self.manager.custom_screens["straight"],
                          self.manager.custom_screens["lucid"],
                          self.manager.custom_screens["lucid"],
                          self.manager.custom_screens["lucid"],
                          self.manager.get_last_screen()]
            self.next_screen = self.stack[len(self.stack) - 1]
            self.stack[len(self.stack) - 1].prev_screen = self

    def changed(self, number, *args):
        if args[1]:
            self.stack_usage[number] = True
        else:
            self.stack_usage[number] = False
        for i in range(0, len(self.stack_usage)):
            if self.stack_usage[i]:
                self.next_screen = self.stack[i]
                self.stack[i].prev_screen = self
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
            last_screen = self
            if self.ids["straight_success_count"].text_input.text and self.ids["straight_success"].is_checked:
                tuple_screens = self.create_screens("straight", int(self.ids["straight_success_count"].text_input.text))
                last_screen = tuple_screens[1]
                self.next_screen = tuple_screens[0]
                tuple_screens[0].prev_screen = self
            next_screen = self.manager.get_next_screen("straight")
            last_screen.next_screen = next_screen
            next_screen.prev_screen = last_screen
            self.manager.switch_to(self.next_screen, direction="left")
            return
        content = []
        if not technique_set:
            content.append("Укажите тип используемых прямых техник")
        if not num_success_set:
            content.append("Укажите количество выходов")
        self.show_popup(*content)

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


class LucidScreen(ScreenTemplate):

    def __init__(self, **kwargs):
        super(LucidScreen, self).__init__(**kwargs)
        self.in_out = True

    def next(self):
        quality_set = self.ids["dream_quality"].text_input.text
        lucid_text = self.ids["number_of_lucid_dreams"].text_input.text
        is_lucid_disabled = self.ids["number_of_lucid_dreams"].disabled
        indirect_text = self.ids["number_of_indirect_tries"].text_input.text
        is_indirect_disabled = self.ids["number_of_indirect_tries"].disabled
        content = []
        if not quality_set:
            content.append('Укажите качество сна')
        else:
            self.next_screen = self.manager.get_last_screen()
            self.next_screen.prev_screen = self
        if is_indirect_disabled or indirect_text:
            self.screen_update(indirect_text, "indirect")
            if is_lucid_disabled or lucid_text:
                self.screen_update(lucid_text, "lucid")
            self.manager.switch_to(self.next_screen, direction="left")
            return
        if not (lucid_text or is_lucid_disabled):
            content.append('Укажите количество осознаний во сне')
        if not (indirect_text or is_indirect_disabled):
            content.append('Укажите количество непрямых попыток')
        self.show_popup(*content)

    def on_enter(self, *args):
        self.next_screen = self.manager.get_last_screen()
        if self.in_out:
            self.ids["dream_quality"].text_input.text = \
                self.ids["number_of_lucid_dreams"].text_input.text = \
                self.ids["number_of_indirect_tries"].text_input.text = ""
        self.in_out = not self.in_out

    def screen_update(self, text, screen_type):
        if text:
            screen_tuple = self.create_screens(screen_type, int(text))
            first_screen = screen_tuple[0]
            last_screen = screen_tuple[1]
            next_screen = self.next_screen
            self.next_screen = first_screen
            first_screen.prev_screen = self
            last_screen.next_screen = next_screen
            next_screen.prev_screen = last_screen

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


class IndirectScreen(ScreenTemplate):
    #TODO сделать отслеживание чекбоксов, чтобы включались/отключались другие опции
    def __init__(self, **kwargs):
        super(IndirectScreen, self).__init__(**kwargs)
        self.have_next_screen = False
        self.after_init()
        self.disabled_dict = {}

    def after_init(self):
        self.ids["try_division"].bind(is_checked=self.switch_everything)
        self.ids["undesired_asleep"].bind(is_checked=self.switch_everything)
        self.ids["desired_asleep"].bind(is_checked=self.switch_everything)
        self.ids["division_exit"].bind(is_checked=self.switch_everything)
        self.ids["technique_exit"].bind(is_checked=self.switch_everything)

    def switch_everything(self, widget, value):
        try_division = self.ids["try_division"].is_checked
        division_exit = self.ids["division_exit"].is_checked
        div_names = ["number_of_cycles", "technique_exit", "undesired_asleep", "desired_asleep"]
        technique_exit = self.ids["technique_exit"].is_checked
        tech_names = ["desired_asleep", "undesired_asleep"]
        self.ids["division_exit"].disabled = not try_division
        if not try_division:
            for name in div_names:
                self.ids[name].disabled = False
            if technique_exit:
                for name in tech_names:
                    self.ids[name].disabled = technique_exit
            else:
                self.ids["desired_asleep"].disabled = self.ids["undesired_asleep"].is_checked
                self.ids["undesired_asleep"].disabled = self.ids["desired_asleep"].is_checked
            return
        self.ids["undesired_asleep"].disabled = self.ids["desired_asleep"].is_checked
        self.ids["desired_asleep"].disabled = self.ids["undesired_asleep"].is_checked
        if division_exit:
            for name in div_names:
                self.ids[name].disabled = division_exit
        else:
            self.ids["number_of_cycles"].disabled = self.ids["technique_exit"].disabled = False
            if technique_exit:
                for name in tech_names:
                    self.ids[name].disabled = technique_exit
            else:
                self.ids["desired_asleep"].disabled = self.ids["undesired_asleep"].is_checked
                self.ids["undesired_asleep"].disabled = self.ids["desired_asleep"].is_checked

    def next(self):
        brightness = self.ids["brightness"].text_input.text
        cycles_text = self.ids["number_of_cycles"].text_input.text
        num_cycles = cycles_text or cycles_text == "0"
        if brightness and num_cycles:
            self.prepare_next_screen()
            self.manager.switch_to(self.next_screen, direction="left")
            return
        content = []
        if not brightness:
            content.append('Укажите яркость пробуждения')
        if not num_cycles:
            content.append('Укажите количество циклов техник')
        self.show_popup(*content)

    def prepare_next_screen(self):
        is_exit = self.ids["division_exit"].is_checked or self.ids["technique_exit"].is_checked
        if is_exit and self.have_next_screen:
            pass
        elif is_exit:
            screen = ExitScreen(screen_type="Непрямой выход", name=self.name+"exit")
            next_screen = self.next_screen
            next_screen.prev_screen = screen
            screen.next_screen = next_screen
            self.next_screen = screen
            screen.prev_screen = self
            self.manager.custom_screens[screen.name] = screen
            self.have_next_screen = True
        elif self.have_next_screen:
            screen = self.next_screen
            next_screen = screen.next_screen
            self.next_screen = next_screen
            next_screen.prev_screen = self
            self.manager.custom_screens.pop(screen.name)
            self.have_next_screen = False
        else:
            pass

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
    repetition = NumericProperty()

    def __init__(self, **kwargs):
        super(ExitScreen, self).__init__(**kwargs)
        self.ids["screen_type"].text = kwargs["screen_type"]
        self.ids["was_repeated_success"].bind(is_checked=self.repeated_exit_changed)

    def find_last_screen(self):
        if "repeated" not in self.next_screen.name:
            return self.next_screen
        else:
            return self.next_screen.find_last_screen()

    def repeated_exit_changed(self, widget, value):
        if value:
            screen = ExitScreen(screen_type="Повторный выход",
                                name=self.name+"repeated",
                                repetition=(self.repetition + 1))
            next_screen = self.next_screen
            self.next_screen = screen
            screen.prev_screen = self
            screen.next_screen = next_screen
            next_screen.prev_screen = screen
            self.manager.custom_screens[screen.name] = screen
        else:
            next_screen = self.find_last_screen()
            self.next_screen = next_screen
            next_screen.prev_screen = self



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
        self.check_box.bind(active=self.is_checked_change)
        self.bind(is_checked=self.is_checked_change)
        self.is_checked = False
        self.ids["label"].text = self.label_text

    def is_checked_change(self, widget, value):
        if value:
            self.is_checked = True
            if widget is not self.check_box:
                self.check_box.active = True
        else:
            self.is_checked = False
            if widget is not self.check_box:
                self.check_box.active = False

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

    def get_last_screen(self):
        return self.custom_screens["last"]

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
                screen = self.custom_screens["lucid"].create_indirect_wakes_screens()
                return screen
            else:
                return self.custom_screens["last"]
        if screen_name == "indirect":
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
        #self.sm.switch_to(self.sm.custom_screens["main_menu"])
        self.sm.switch_to(self.sm.custom_screens["indirect"])
        return self.sm


if __name__ == '__main__':
    AingerDiaryApp().run()
