import kivy
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from datetime import date, timedelta
from functools import partial
import calendar
kivy.require('1.4.0')


class DatePicker(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(DatePicker, self).__init__(**kwargs)
        self.date = date.today()
        self.orientation = "vertical"
        self.month_names = ('Январь',
                            'Февраль',
                            'Март',
                            'Апрель',
                            'Май',
                            'Июнь',
                            'Июль',
                            'Август',
                            'Сентябрь',
                            'Октябрь',
                            'Ноябрь',
                            'Декабрь')
        if"month_names" in kwargs:
            self.month_names = kwargs['month_names']
        self.header = BoxLayout(orientation='horizontal',
                                size_hint=(1, 0.2))
        self.body = GridLayout(cols=7)
        self.add_widget(self.header)
        self.add_widget(self.body)

        self.populate_body()
        self.populate_header()

    def populate_header(self, *args, **kwargs):
        self.header.clear_widgets()
        previous_month = Button(text="<")
        previous_month.bind(on_press=partial(self.move_previous_month))
        next_month = Button(text=">")
        next_month.bind(on_press=partial(self.move_next_month))
        month_year_text = self.month_names[self.date.month - 1] + ' ' + str(self.date.year)
        current_month = Label(text=month_year_text, size_hint=(2, 1))

        self.header.add_widget(previous_month)
        self.header.add_widget(current_month)
        self.header.add_widget(next_month)

    def populate_body(self, *args, **kwargs):
        self.body.clear_widgets()
        date_cursor = date(self.date.year, self.date.month, 1)
        for filler in range(date_cursor.isoweekday() - 1):
            self.body.add_widget(Label(text=""))
        while date_cursor.month == self.date.month:
            date_label = Button(text=str(date_cursor.day))
            date_label.bind(on_press=partial(self.set_date,
                                             day=date_cursor.day))
            if self.date.day == date_cursor.day:
                date_label.background_normal, \
                    date_label.background_down = date_label.background_down, date_label.background_normal
            self.body.add_widget(date_label)
            date_cursor += timedelta(days=1)

    def set_date(self, *args, **kwargs):
        self.date = date(self.date.year, self.date.month, kwargs['day'])
        self.populate_body()
        self.populate_header()

    def move_next_month(self, *args, **kwargs):
        if self.date.month == 12:
            self.date = date(self.date.year + 1, 1, self.date.day)
        else:
            self.date = date(self.date.year, self.date.month + 1,
                             min(self.date.day, calendar.monthrange(self.date.year, self.date.month + 1)[1]))
        self.populate_header()
        self.populate_body()

    def move_previous_month(self, *args, **kwargs):
        if self.date.month == 1:
            self.date = date(self.date.year - 1, 12, self.date.day)
        else:
            self.date = date(self.date.year, self.date.month - 1,
                             min(self.date.day, calendar.monthrange(self.date.year, self.date.month - 1)[1]))
        self.populate_header()
        self.populate_body()
