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
import sqlite3
import os

__author__ = "Unencrypted"


class ScreenTemplate(Screen):
    next = ObjectProperty(None)
    prev = ObjectProperty(None)

    def switch(self, direction, screen):
        self.manager.switch_to(self.manager.custom_screens[screen], direction=direction)

    def next(self):
        pass

    def prev(self):
        pass

class MainScreen(ScreenTemplate):
    def go_try(self):
        self.switch("ask_date", "left")

    def go_show(self):
        self.switch("show", "left")


class ShowScreen(ScreenTemplate):
    pass


class TechniqueScreen(ScreenTemplate):
    def __init__(self, **kwargs):
        super(TechniqueScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        self.ids["ask_dream"].check_box.bind(active=self.dream_changed)

    def dream_changed(self, widget, is_disabled):
        if is_disabled:
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = False
        else:
            self.ids["ask_lucid"].check_box.active = self.ids["ask_indirect"].check_box.active = False
            self.ids["ask_lucid"].disabled = self.ids["ask_indirect"].disabled = True

    def collect_data(self):
        return_dict = dict()
        return_dict["straight"] = self.ids["ask_straight"].is_checked
        return_dict["lucid"] = self.ids["ask_dream"].is_checked
        return_dict["indirect"] = self.ids["ask_indirect"].is_checked
        return return_dict


class AskDateScreen(ScreenTemplate):
    pick = ObjectProperty(None)


class StraightScreen(ScreenTemplate):
    def next(self):
        technique_set = self.ids["cycle"].active \
                        or self.ids["alternation"].active \
                        or self.ids["one_technique"].active
        num_success_set = self.ids["straight_success"].is_checked \
                          and self.ids["straight_success_count"].text_input.text \
                          or not self.ids["straight_success"].is_checked
        if technique_set and num_success_set:
            self.manager.straight_next()
            return
        content = BoxLayout(orientation='vertical')
        button = Button(text='Закрыть', size_hint=(None, 0.2), pos_hint={'center_x': 0.5})
        label = Label(text='Укажите тип используемых прямых техник')
        label2 = Label(text='Укажите количество выходов')
        popup = Popup(title='Ошибка', content=content, size_hint=(0, 0), size=(400, 400))
        button.bind(on_press=popup.dismiss)
        content.clear_widgets()
        if not technique_set:
            content.add_widget(label)
        if not num_success_set:
            content.add_widget(label2)
        content.add_widget(button)
        popup.open()

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

    def next(self):
        quality_set = self.ids["dream_quality"].text_input.text
        lucid_number = self.ids["number_of_lucid_dreams"].text_input.text
        is_lucid_disabled = self.ids["number_of_lucid_dreams"].disabled
        indirect_number = self.ids["number_of_indirect_tries"].text_input.text
        is_indirect_disabled = self.ids["number_of_indirect_tries"].disabled
        if quality_set \
                and (is_lucid_disabled or (lucid_number and not is_lucid_disabled)) \
                and (is_indirect_disabled or (indirect_number and not is_indirect_disabled)):
                self.manager.lucid_next()
                return
        content = BoxLayout(orientation='vertical')
        button = Button(text='Закрыть', size_hint=(None, 0.2), pos_hint={'center_x': 0.5})
        label = Label(text='Укажите качество сна')
        label2 = Label(text='Укажите количество осознаний во сне')
        label3 = Label(text='Укажите количество непрямых попыток')
        popup = Popup(title='Ошибка', content=content, size_hint=(0, 0), size=(400, 400))
        button.bind(on_press=popup.dismiss)
        content.clear_widgets()
        if not quality_set:
            content.add_widget(label)
        if not lucid_number and not is_lucid_disabled:
            content.add_widget(label2)
        if not indirect_number and not is_indirect_disabled:
            content.add_widget(label3)
        content.add_widget(button)
        popup.open()

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

    def next(self):
        brightness = self.ids["brightness"].text_input.text
        cycles_text = self.ids["number_of_cycles"].text_input.text
        num_cycles = cycles_text or cycles_text == "0"
        if brightness and num_cycles:
            self.manager.indirect_next()
            return
        content = BoxLayout(orientation='vertical')
        button = Button(text='Закрыть', size_hint=(None, 0.2), pos_hint={'center_x': 0.5})
        label = Label(text='Укажите яркость пробуждения')
        label2 = Label(text='Укажите количество циклов техник')
        popup = Popup(title='Ошибка', content=content, size_hint=(0, 0), size=(400, 400))
        button.bind(on_press=popup.dismiss)
        content.clear_widgets()
        if not brightness:
            content.add_widget(label)
        if not num_cycles:
            content.add_widget(label2)
        content.add_widget(button)
        popup.open()

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

    def switch_show(self):
        self.switch_to(self.custom_screens["show"], direction="left")

    def switch_date(self):
        self.switch_to(self.custom_screens["ask_date"], direction="left")

    def ask_date_prev(self):
        self.switch_to(self.custom_screens["main_menu"], direction="right")

    def ask_date_next(self):
        self.switch_to(self.custom_screens["technique"], direction="left")

    def technique_prev(self):
        self.switch_to(self.custom_screens["ask_date"], direction="right")

    def technique_next(self):
        self.straight_present = self.dream_present = self.lucid_present = self.indirect_present = False
        tech = self.get_screen("technique")
        if tech.ids["ask_dream"].is_checked:
            self.dream_present = True
            if tech.ids["ask_indirect"].is_checked:
                self.indirect_present = True
                self.custom_screens["lucid"].switch_indirect(True)
                self.switch_to(self.custom_screens["lucid"], direction="left")
            else:
                self.custom_screens["lucid"].switch_indirect(False)
            if tech.ids["ask_lucid"].is_checked:
                self.lucid_present = True
                self.custom_screens["lucid"].switch_lucid(True)
                if self.current_screen != self.custom_screens["lucid"]:
                    self.switch_to(self.custom_screens["lucid"], direction="left")
            else:
                self.custom_screens["lucid"].switch_lucid(False)
        if tech.ids["ask_straight"].is_checked:
            self.straight_present = True
            self.switch_to(self.custom_screens["straight"], direction="left")

    def straight_next(self):
        if self.lucid_present:
            self.switch_to(self.custom_screens["lucid"], direction="left")
        else:
            self.lucid_next()

    def lucid_next(self):
        if self.indirect_present:
            self.switch_to(self.custom_screens["indirect"], direction="left")
        else:
            self.indirect_next()

    def indirect_next(self):
        self.compute_exit_screens()

    def straight_prev(self):
        self.switch_to(self.custom_screens["technique"], direction="right")

    def lucid_prev(self):
        if self.straight_present:
            self.switch_to(self.custom_screens["straight"], direction="right")
        else:
            self.straight_prev()

    def indirect_prev(self):
        if self.lucid_present:
            self.switch_to(self.custom_screens["lucid"], direction="right")
        else:
            self.lucid_prev()

    def exit_next(self):
        pass

    def exit_prev(self):
        pass

    def compute_indirect_screens(self):
        lucid_data = self.custom_screens["lucid"].collect_data()
        number_of_indirect_tries = lucid_data["indirect_number"]
        for i in number_of_indirect_tries:
            self.custom_screens["indirect" + str(i)] = ExitScreen(name="indirect" + str(i))


    def compute_exit_screens(self):
        technique_data = self.custom_screens["technique"].collect_data()

        print("NotImplementedYet")


class AingerDiaryApp(App):
    def __init__(self, **kwargs):
        super(AingerDiaryApp, self).__init__(**kwargs)
        self.sm = WindowManager()

    def build(self):
        self.sm.custom_screens["main_menu"] = (MainScreen(name="main_menu"))
        self.sm.custom_screens["show"] = (ShowScreen(name="show",
                                                     prev=self.sm.custom_screens["main_menu"]))
        self.sm.custom_screens["ask_date"] = (AskDateScreen(name="ask_date",
                                                            prev=self.sm.custom_screens["main_menu"]))
        self.sm.custom_screens["technique"] = (TechniqueScreen(name="technique",
                                                               prev=self.sm.custom_screens["ask_date"]))
        self.sm.custom_screens["ask_date"].next = self.sm.custom_screens["technique"]
        self.sm.custom_screens["straight"] = (StraightScreen(name="straight", prev=self.sm.custom_screens["technique"]))
        self.sm.custom_screens["lucid"] = (LucidScreen(name="lucid"))
        self.sm.custom_screens["indirect"] = (IndirectScreen(name="indirect"))
        self.sm.switch_to(self.sm.custom_screens["main_menu"])
        return self.sm


if __name__ == '__main__':
    AingerDiaryApp().run()
