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
connection = None
cursor = None


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
        type_typos = {"straight": "exit", "lucid": "exit", "indirect": ""}
        to_remove = []
        for screen in self.manager.custom_screens:
            if screen.startswith(screen_type) and not (screen == screen_type):
                to_remove.append(screen)
        for screen in to_remove:
            self.manager.custom_screens.pop(screen, None)
        return_screen = new_screen = types[screen_type](name=screen_type + "0" + type_typos[screen_type], screen_type=type_names[screen_type])
        self.manager.custom_screens[new_screen.name] = new_screen
        new_screen.prev_screen = self
        last_screen = new_screen
        for i in range(0, count - 1):
            new_screen = types[screen_type](name=(screen_type + str(i + 1) + type_typos[screen_type]), screen_type=type_names[screen_type])
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
    # TODO сделать экран с отображением графика

    def __init__(self, **kwargs):
        super(ShowScreen, self).__init__(**kwargs)

    def on_enter(self, *args):
        self.draw_screen()

    # def get_repeated_exit(self, exit_id):
    #     command = "SELECT * FROM exits e1 INNER JOIN exits e2 ON WHERE id = ?"
    #     cursor.execute(command, exit_id)
    #     current_exit = cursor.fetchone()
    #     if current_exit[3] is not None:
    #         return current_exit + self.get_repeated_exit(current_exit[3])
    #     else:
    #         return

    # def get_statistics(self, date_start, date_stop):
    #     date_score_dict = {}
    #     repeated_exits = []
    #     straight = self.get_straight(date_start, date_stop)
    #     lucid = self.get_lucid(date_start, date_stop)
    #     indirect_tuple = self.get_indirect(date_start, date_stop)
    #     exits = straight + lucid + indirect_tuple[0]
    #     if exits:
    #         for current_exit in exits:
    #             if current_exit[3] is not None:
    #                 repeated_exits + self.get_repeated_exit(current_exit[3])
    #         exits += repeated_exits
    #         for phase_exit in exits:
    #             exit_date = phase_exit[9]
    #             if exit_date not in date_score_dict:
    #                 date_score_dict[exit_date] = 0
    #             date_score_dict[exit_date] += self.calculate_exit(phase_exit)
    #     indirect_tries = indirect_tuple[1]
    #     for indirect_try in indirect_tries:
    #         pass
    def newlines(self):
        pass




    def calculate_exit(self, phase_exit):
        current_score = 0
        exit_type = phase_exit[1]
        current_score += self.exit_type_translation[exit_type]
        was_deepening = phase_exit[4]
        if was_deepening:
            current_score += self.exit_translation["deepening"]
        was_holding = phase_exit[5]
        if was_holding:
            current_score += self.exit_translation["holding"]
        current_score += self.exit_translation["plan_items_done"] * phase_exit[6]
        catch_try = phase_exit[7]
        if catch_try:
            current_score += self.exit_translation["catch_try"]
        return current_score


    def get_indirect(self, date_start, date_stop):
        command = "SELECT * FROM exits" \
                  "INNER JOIN global_try ON exits.global_try_id = global_try.id" \
                  "WHERE type = 2 " \
                  "AND date >= ? AND date <= ?;"
        cursor.execute(command, (date_start, date_stop))
        exits = cursor.fetchall()
        command = "SELECT * FROM indirect" \
                  "INNER JOIN global_try ON indirect.global_try_id = global_try.id" \
                  "WHERE date >= ? AND date <= ?;"
        cursor.execute(command, (date_start, date_stop))
        indirect = cursor.fetchall()
        return exits, indirect,

    def get_lucid(self, date_start, date_stop):
        command = "SELECT * FROM exits " \
                  "INNER JOIN global_try ON exits.global_try_id = global_try.id" \
                  "WHERE type = 1" \
                  "AND date >= ? AND date <= ?"
        cursor.execute(command, (date_start, date_stop))
        exits = cursor.fetchall()
        return exits

    def get_straight(self, date_start, date_stop):
        command = "SELECT * FROM exits " \
                  "INNER JOIN global_try ON exits.global_try_id = global_try.id" \
                  "WHERE type = 0" \
                  "AND date >= ? AND date <= ?"
        cursor.execute(command, (date_start, date_stop))
        exits = cursor.fetchall()
        return exits



    def calculate_points(self, things_array):
        pass

class TrainingScreen(ScreenTemplate):
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
                          and self.ids["straight_success_count"].text \
                          or not self.ids["straight_success"].is_checked
        if technique_set and num_success_set:
            last_screen = self
            if self.ids["straight_success_count"].text and self.ids["straight_success"].is_checked:
                tuple_screens = self.create_screens("straight", int(self.ids["straight_success_count"].text))
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
            return_dict["number"] = int(self.ids["straight_success_count"].text)
        else:
            return_dict["success"] = False
        return return_dict


class LucidScreen(ScreenTemplate):

    def __init__(self, **kwargs):
        super(LucidScreen, self).__init__(**kwargs)

    def next(self):
        quality_set = self.ids["dream_quality"].text
        lucid_text = self.ids["number_of_lucid_dreams"].text
        is_lucid_disabled = self.ids["number_of_lucid_dreams"].disabled
        indirect_text = self.ids["number_of_indirect_tries"].text
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
        self.ids["dream_quality"].text = \
            self.ids["number_of_lucid_dreams"].text = \
            self.ids["number_of_indirect_tries"].text = ""

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
        return_dict["quality"] = self.ids["dream_quality"].text
        if self.ids["number_of_lucid_dreams"].text:
            return_dict["lucid_number"] = int(self.ids["number_of_lucid_dreams"].text)
        if self.ids["number_of_indirect_tries"].text:
            return_dict["indirect_number"] = int(self.ids["number_of_indirect_tries"].text)
        return return_dict


class IndirectScreen(ScreenTemplate):
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
        brightness = self.ids["brightness"].text
        cycles_text = self.ids["number_of_cycles"].text
        num_cycles = (cycles_text or cycles_text == "0") or self.ids["number_of_cycles"].disabled
        legitimate_cycles = not (cycles_text == "0" and self.ids["technique_exit"].is_checked)
        if brightness and num_cycles and legitimate_cycles:
            self.prepare_next_screen()
            self.manager.switch_to(self.next_screen, direction="left")
            return
        content = []
        if not brightness:
            content.append('Укажите яркость пробуждения')
        if not num_cycles:
            content.append('Укажите количество циклов техник')
        if not legitimate_cycles:
            content.append('Нельзя выйти при помощи техник, не используя техники :/')
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
        return_dict.brightness = int(self.ids["brightness"].text)
        return_dict.move = self.ids["was_moving"].is_checked
        return_dict.division = self.ids["try_division"].is_checked
        if return_dict.division:
            return_dict.success_division = self.ids["success_division"].is_checked
            if return_dict.success_division:
                return return_dict
        return_dict.num_cycles = int(self.ids["number_of_cycles"].text)
        return_dict.tech_exit = self.ids["technique_exit"].is_checked
        if return_dict.tech_exit:
            return return_dict
        return_dict.undesired_asleep = self.ids["undesired_asleep"].is_checked
        if not return_dict.undesired_asleep:
            return_dict.desired_asleep = self.ids["desired_asleep"].is_checked
        return return_dict


class ExitScreen(ScreenTemplate):
    repetition = NumericProperty()
    type = NumericProperty()

    def __init__(self, **kwargs):
        super(ExitScreen, self).__init__(**kwargs)
        screen_type = kwargs["screen_type"]
        self.ids["screen_type"].text = screen_type
        if screen_type == "Прямой выход":
            self.type = 0
        elif screen_type == "Осознание во сне":
            self.type = 1
        elif screen_type == "Непрямой выход":
            self.type = 2
        elif screen_type == "Повторный выход":
            self.type = 3
        self.ids["was_repeated_success"].bind(is_checked=self.repeated_exit_changed)
        self.after_init()

    def after_init(self):
        self.ids["was_repeated_try"].bind(is_checked=self.change_repeated_success)

    def change_repeated_success(self, widget, value):
        self.ids["was_repeated_success"].disabled = not value

    def next(self):
        if not self.ids["items_done"].text:
            self.show_popup("Укажите количество выполненных пунктов плана действий")
            return
        else:
            self.manager.switch_to(self.next_screen, direction="left")

    def find_last_screen(self):
        if "repeated" not in self.next_screen.name:
            return self.next_screen
        else:
            return self.next_screen.find_last_screen()

    def repeated_exit_changed(self, widget, value):
        if value:
            screen = ExitScreen(screen_type="Повторный выход",
                                name=self.name+"repeated_exit",
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


class SetStatisticsScreen(ScreenTemplate):
    def __init__(self, **kwargs):
        super(SetStatisticsScreen, self).__init__(**kwargs)
        self.aggression = None
        self.mechanic = None
        self.confidence = None
        self.at_all_costs = None
        self.intention = None
        self.straight_translation = {}
        self.lucid_translation = {}
        self.indirect_translation = {}
        self.exit_type_translation = {0: 2000, 1: 1700, 2: 1200, 3: 1500}
        self.exit_translation = {"deepening": 175, "holding": 125, "plan_items_done": 400, "catch_try": 200}

    def calculate_exit(self, exit_type, was_deepening, was_holding, plan_items_done, catch_try):
        current_score = 0
        current_score += self.exit_type_translation[exit_type]
        if was_deepening:
            current_score += self.exit_translation["deepening"]
        if was_holding:
            current_score += self.exit_translation["holding"]
        current_score += self.exit_translation["plan_items_done"] * plan_items_done
        if catch_try:
            current_score += self.exit_translation["catch_try"]
        return current_score

    def calculate_indirect_try(self, was_moving, was_division, num_cycles, sleep_char):
        score = 0
        if was_moving and was_division:
            score -= 50
        elif was_moving:
            score -= 25
        elif was_division:
            score += 75
        else:
            pass
        if num_cycles > 4:
            score += 75
        else:
            score += 35 * num_cycles
        if sleep_char == 0:
            score -= 35
        elif sleep_char == 1:
            score += 50
        else:
            pass
        return score

    def get_basic_variables(self):
        aggression_text = self.ids["aggression"].text
        mechanic_text = self.ids["mechanic"].text
        confidence_text = self.ids["confidence"].text
        at_all_costs_text = self.ids["at_all_costs"].text
        intention_text = self.ids["intention"].text
        return self.calculate_popup(aggression_text, mechanic_text, confidence_text, at_all_costs_text, intention_text)

    def calculate_popup(self, aggression_text, mechanic_text, confidence_text, at_all_costs_text, intention_text):
        if not (aggression_text and mechanic_text and
                confidence_text and at_all_costs_text and intention_text):
            content = []
            if not aggression_text:
                content.append("Укажите значение агрессии")
            if not mechanic_text:
                content.append("Укажите значение механичности")
            if not confidence_text:
                content.append("Укажите значение уверенности")
            if not at_all_costs_text:
                content.append("Укажите значение \"во что бы то ни стало\"")
            if not intention_text:
                content.append("Укажите значение намерения выйти в фазу")
            self.show_popup(*content)
            return False
        else:
            self.aggression = int(aggression_text)
            self.mechanic = int(mechanic_text)
            self.confidence = int(confidence_text)
            self.at_all_costs = int(at_all_costs_text)
            self.intention = int(intention_text)
            return True

    def on_enter(self, *args):
        self.intention = self.at_all_costs = self.aggression = self.confidence = self.mechanic = None
        self.ids["aggression"].text = self.ids["mechanic"].text = self.ids["confidence"].text = \
            self.ids["at_all_costs"].text = self.ids["intention"].text = ""

    def insert_global_try(self, cursor):
        date = self.manager.custom_screens["ask_date"].ids["pick"].date.isoformat()
        command = "INSERT INTO  global_try (intention, confidence, aggression, mecha, at_all_costs, date)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(command, (self.intention, self.confidence, self.aggression,
                                 self.mechanic, self.at_all_costs, date))

    def next(self):
        if not self.get_basic_variables():
            return
        cursor = connection.cursor()
        screen = self.manager.custom_screens["technique"]
        command = ""
        sleep_quality = None
        indirect_id = None
        self.insert_global_try(cursor)
        cursor.execute("SELECT last_insert_rowid()")
        global_try_id = cursor.fetchone()[0]
        indirect_score = 0
        straight_score = 0
        lucid_score = 0
        repeated_score = 0
        training_score = 0
        while screen != self:
            if "indirect" in screen.name and "exit" not in screen.name:
                brightness = int(screen.ids["brightness"].text)
                moving = screen.ids["was_moving"].is_checked
                division = screen.ids["try_division"].is_checked
                num_cycles = 0
                if not screen.ids["division_exit"].is_checked:
                    num_cycles = int(screen.ids["number_of_cycles"].text)
                sleep_char = None
                if screen.ids["undesired_asleep"].is_checked:
                    sleep_char = 0
                elif screen.ids["desired_asleep"].is_checked:
                    sleep_char = 1
                else:
                    sleep_char = 2
                command = "INSERT INTO indirect_try (global_try_id, brightness, moving," \
                          " division, num_cycles, sleep_char) VALUES(?, ?, ?, ?, ?, ?)"
                cursor.execute(command, (global_try_id, brightness, moving, division, num_cycles, sleep_char))
                cursor.execute("SELECT last_insert_rowid()")
                indirect_id = cursor.fetchone()[0]
                indirect_score += self.calculate_indirect_try(moving, division, num_cycles, sleep_char)
            elif "exit" in screen.name:
                exit_id = None
                tech_type = None
                deepening = screen.ids["was_deepening"].is_checked
                holding = screen.ids["was_holding"].is_checked
                plan_done = int(screen.ids["items_done"].text)
                catch_try = screen.ids["was_catch"].is_checked
                repeated = screen.ids["was_repeated_try"].is_checked
                if screen.type == 0:  # straight
                    tech_type = 0
                elif screen.type == 1:  # lucid
                    tech_type = 1
                elif screen.type == 2:  # indirect
                    tech_type = 2
                else:  # repeated
                    tech_type = 3
                command = "SELECT id FROM exits WHERE id = (SELECT last_insert_rowid())"
                cursor.execute(command)
                parent_id = cursor.fetchone()[0]
                command = "INSERT INTO exits (type, global_try_id, exit_id, deepening," \
                          " holding, plan_done, catch_try, repeated, indirect_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                cursor.execute(command, (tech_type, global_try_id, exit_id,
                                         deepening, holding, plan_done, catch_try, repeated, indirect_id))
                score = self.calculate_exit(tech_type, deepening, holding, plan_done, catch_try)
                if tech_type == 0:
                    straight_score += score
                elif tech_type == 1:
                    lucid_score += score
                elif tech_type == 2:
                    indirect_score += score
                elif tech_type == 3:
                    repeated_score += score
                    command = "SELECT last_insert_rowid()"
                    cursor.execute(command)
                    new_insert_id = cursor.fetchone()[0]
                    command = "UPDATE exits SET exit_id = ? WHERE id = ?"
                    cursor.execute(command, (new_insert_id, parent_id))
            elif screen.name == "lucid":
                sleep_quality = int(screen.ids["dream_quality"].text)
                command = "UPDATE global_try SET dream_quality = ? WHERE id = ?"
                cursor.execute(command, (sleep_quality, global_try_id))
            screen = screen.next_screen
        command = "INSERT INTO cached_points (indirect_score, lucid_score, straight_score, " \
                  "repeated_score, training_score, date) VALUES (?, ?, ?, ?, ?, ?);"
        cursor.execute(command, (indirect_score, lucid_score, straight_score, repeated_score, training_score,
                                 self.manager.custom_screens["ask_date"].ids["pick"].date.isoformat()))
        connection.commit()
        self.manager.switch_to(self.next_screen, direction="left")


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


class AskTextWidget(BoxLayout):
    label_text = StringProperty()
    text = StringProperty(allownone=True)

    def __init__(self, **kwargs):
        super(AskTextWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.after_init, 0)

    def after_init(self, *args):
        self.ids["label"].text = self.label_text
        self.bind(text=self.on_text)
        self.ids["text_input"].bind(text=self.on_text_input)

    def on_text(self, widget, value):
        self.ids["text_input"].text = value

    def on_text_input(self, widget, value):
        self.text = value

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
        self.bind(text=self.check)

    def check(self, *args):
        buffer = ""
        for character in self.text:
            if character.isdigit():
                buffer += character
        if buffer:
            if int(buffer) < self.minimum:
                buffer = str(self.minimum)
            if self.maximum and int(buffer) > self.maximum:
                buffer = str(self.maximum)
            buffer = str(int(buffer))
        self.text = buffer


class WindowManager(ScreenManager):
    num_wakes = 0
    custom_screens = {}
    straight_present = False
    dream_present = False
    lucid_present = False
    indirect_present = False

    def __init__(self):
        global connection, cursor
        super(WindowManager, self).__init__()
        base_path = os.getcwd() + os.sep + "AingerDiary.db"
        connection = sqlite3.connect(base_path)
        cursor = connection.cursor()

    def set_lucid(self, is_enabled):
        self.custom_screens["lucid"].ids["number_of_lucid_dreams"].disabled = not is_enabled

    def set_indirect(self, is_enabled):
        self.custom_screens["lucid"].ids["number_of_indirect_tries"].disabled = not is_enabled

    def switch_show(self):
        self.switch_to(self.custom_screens["show"], direction="left")

    def switch_date(self):
        self.switch_to(self.custom_screens["ask_date"], direction="left")

    def get_last_screen(self):
        return self.custom_screens["statistics"]

    def get_next_screen(self, screen_name):
        data = self.custom_screens["technique"].collect_data()
        if screen_name == "straight":
            if data["lucid"] or data["indirect"]:
                return self.custom_screens["lucid"]
            else:
                return self.get_last_screen()
        if screen_name == "lucid":
            lucid_data = self.custom_screens["lucid"].collect_data()
            if "indirect_number" in lucid_data:
                screen = self.custom_screens["lucid"].create_indirect_wakes_screens()
                return screen
            else:
                return self.get_last_screen()
        if screen_name == "indirect":
            return self.get_last_screen()


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
        self.sm.custom_screens["last"] = (EndScreen(name="last"))
        self.sm.custom_screens["statistics"] = SetStatisticsScreen(name="statistics",
                                                                   prev_screen=self.sm.custom_screens["technique"],
                                                                   next_screen=self.sm.custom_screens["last"])
        self.sm.custom_screens["last"].prev_screen = self.sm.custom_screens["main_menu"]
        self.sm.switch_to(self.sm.custom_screens["main_menu"])
        # self.sm.switch_to(self.sm.custom_screens["indirect"])
        return self.sm
        #return ExitScreen(screen_type="тестовый выход", name="new_exit_screen", next_screen=self.sm.custom_screens["indirect"], manager=self.sm)


if __name__ == '__main__':
    AingerDiaryApp().run()
