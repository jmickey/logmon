from datetime import datetime, timezone, timedelta
import time
import logging
import urwid

_logger = logging.getLogger(__name__)


class LineBox2(urwid.LineBox):
    """
    LineBox2 inherits from LineBox, and overrides the set_title
    method in order to allow attributes to be set on the title.
    """

    def set_title(self, title: str, attr: str = None):
        """
        Set the title for the LineBox widget.

        :param title: string containing the desired title.
        :param attr:  string containing the attribute name.
        """
        if not self.title_widget:
            raise ValueError('Cannot set title when tline is unset')
        if attr:
            self.title_widget.set_text(
                (attr, self.format_title(title)))
        else:
            self.title_widget.set_text(self.format_title(title))


class Display:

    def __init__(self, monitor, refresh_rate: float =10.0) -> None:
        """
        The Display class handles UI rendering and operations.

        :param monitor:      (monitor.BaseMonitor) monitor object for
                             retreiving stats and alerts
        :param refresh_rate: (int) update rate for main UI loop
        """
        self.monitor = monitor
        self.refresh_rate = refresh_rate
        self.start_time = time.time()
        _logger.info(f'Application started at {datetime.now(timezone.utc)}')
        self.in_alert = False

        self._init_left_panels()
        self._init_right_panels()

        main_cols = urwid.Columns([self.left_panel, self.right_panel])

        # Header and footer
        title = urwid.Padding(
            urwid.LineBox(urwid.Text(' HTTP Log Monitor')),
            align='center')
        title = urwid.AttrMap(title, 'title')
        keymap = urwid.Padding(
            urwid.LineBox(urwid.Text(' Q: Exit')),
            align='center')
        keymap = urwid.AttrMap(keymap, 'footer')

        self.main = urwid.Frame(main_cols, title, keymap)

        def handle_inputs(input):
            """
            Handle keyboard inputs.
            """
            if input in ('q', 'Q'):
                raise self.close()

        self.event_loop = urwid.MainLoop(self.main, palette=[
            ('title', 'light cyan, bold', 'dark gray'),
            ('heading', 'light magenta, bold', 'default'),
            ('time', 'light blue, bold', 'default'),
            ('white-bold', 'white, bold', 'default'),
            ('alert', 'dark red', 'default'),
            ('recover', 'dark green', 'default'),
            ('green', 'light green', 'default')
            ], unhandled_input=handle_inputs)

        self.event_loop.set_alarm_in(0.1, self.update)
        self.event_loop.set_alarm_in(1, self.update_info)
        self.event_loop.set_alarm_in(1, self.update_summary)
        self.event_loop.set_alarm_in(0.1, self.update_alerts)

    def _init_left_panels(self):
        """
        Initialise panels to be displayed on the left side of the screen.
        """

        # Info panel text
        runtime = timedelta(seconds=(time.time() - self.start_time))
        fmt = '{hours:02}:{minutes:02}:{seconds:02}'
        self.runtime_text = urwid.Text((
            'time', f'{self.strfdelta(runtime, fmt)}'))

        self.info_text_list = [
            urwid.Columns([
                ('weight', 5, urwid.Text('Running time:')),
                ('weight', 11, self.runtime_text)
            ]),
            urwid.Columns([
                ('weight', 5, urwid.Text('Refresh rate:')),
                ('weight', 11, urwid.Text(f'{self.refresh_rate}s'))]),
            urwid.Columns([
                ('weight', 5, urwid.Text('Alert threshold:')),
                ('weight', 11, urwid.Text(
                    f'{self.monitor.alert_threshold}/s'))]),
            urwid.Columns([
                ('weight', 5, urwid.Text('Alert window:')),
                ('weight', 11, urwid.Text(
                    f'{self.monitor.alert_duration}s'))])
        ]

        # Left panel parts - info panel, most visited, summary stats
        self.info_box = LineBox2(
            urwid.Padding(
                urwid.Pile(self.info_text_list),
                width=('relative', 80), align='left', left=1),
            title_align='left')
        self.info_box.set_title('Info', 'heading')

        self.most_visited_headings = urwid.Columns([
            urwid.Text(('white-bold', 'Section')),
            urwid.Text(('white-bold', f'Hits ({self.refresh_rate}s)'))])
        self.most_visited_total = urwid.Columns([
            urwid.Text(('white-bold', 'Total')),
            urwid.Text(('white-bold', ''))])
        self.most_visited_list = urwid.SimpleFocusListWalker([])
        pile = urwid.Pile([
            ('pack', self.most_visited_headings),
            urwid.ListBox(self.most_visited_list),
            ('pack', self.most_visited_total)])
        self.most_visited_box = LineBox2(
            urwid.Padding(
                pile, width=('relative', 80), align='left', left=1),
            title_align='left')
        self.most_visited_box.set_title('Most Visited', 'heading')

        self.total_hits = urwid.Text((
            'green', f'{self.monitor.total_requests}'))
        self.total_traffic = urwid.Text(('green', '0KB'))
        self.average_hits = urwid.Text(('green', '0'))

        self.summary_text = [
            urwid.Columns([
                ('weight', 5, urwid.Text('Total hits:')),
                ('weight', 11, self.total_hits)
            ]),
            urwid.Columns([
                ('weight', 5, urwid.Text('Total traffic (KB):')),
                ('weight', 11, self.total_traffic)]),
            urwid.Columns([
                ('weight', 5, urwid.Text('Average hits (/s)')),
                ('weight', 11, self.average_hits)])
        ]
        self.summary_box = LineBox2(
            urwid.Padding(
                urwid.Pile(self.summary_text),
                width=('relative', 80), align='left', left=1),
            title_align='left')
        self.summary_box.set_title('Summary', 'heading')

        # Stack the left panel sections
        self.left_panel = urwid.Pile(
            [('pack', self.info_box),
             self.most_visited_box,
             ('pack', self.summary_box)])

    def _init_right_panels(self):
        """
        Initialise panels to be displayed on the right side of the screen.
        """

        # Right panel parts - most visited sections and alerts
        self.alerts_text_list = urwid.SimpleFocusListWalker([])
        self.alert_list = urwid.ListBox(self.alerts_text_list)
        self.alerts_box = LineBox2(
            urwid.Padding(
                self.alert_list,
                align='left', left=1),
            title_align='left')
        self.alerts_box.set_title('Alerts', 'heading')

        self.right_panel = urwid.Pile([self.alerts_box])

    def update_alerts(self, event_loop=None, data=None):
        """
        Checks the alerts status and updates the alerts window
        if an alert exists.
        """
        self.monitor.update()
        if self.monitor.alert is not None:
            if not self.in_alert and not self.monitor.alert.recovered:
                self.alerts_text_list.extend(
                    [urwid.Text(('alert', f'{self.monitor.alert}'))])
                self.in_alert = True
            elif self.in_alert and self.monitor.alert.recovered:
                self.alerts_text_list.extend(
                    [urwid.Text(('recover', f'{self.monitor.alert}'))])
                self.in_alert = False
            self.alert_list.focus_position = len(self.alerts_text_list) - 1
        self.event_loop.set_alarm_in(0.1, self.update_alerts)

    def update(self, event_loop=None, data=None):
        """
        Updates the sections.
        """
        self.monitor.update()
        data: list = self.monitor.short_log_data
        sections: dict = {}
        for line in data:
            if line.section in sections.keys():
                sections[line.section] += 1
            else:
                sections[line.section] = 1
        self.most_visited_list.clear()
        total: int = 0
        for section in sorted(sections.items()):
            col = urwid.Columns([])
            col.contents.append((
                urwid.Text(f'{section[0]}'), col.options()))
            col.contents.append((
                urwid.Text(f'{section[1]}'), col.options()))
            total += section[1]
            self.most_visited_list.extend([col])
        self.most_visited_total.contents[1][0].set_text(str(total))
        self.event_loop.set_alarm_in(self.refresh_rate, self.update)

    def update_info(self, event_loop=None, data=None):
        """
        Updates runtime and total hits.
        """
        runtime = timedelta(seconds=(time.time() - self.start_time))
        fmt = '{hours:02}:{minutes:02}:{seconds:02}'
        self.runtime_text.set_text((
            'time',
            f'{self.strfdelta(runtime, fmt)}'))
        self.event_loop.set_alarm_in(1, self.update_info)

    def update_summary(self, event_loop=None, data=None):
        self.total_hits.set_text(('green', f'{self.monitor.total_requests}'))
        self.total_traffic.set_text(
            ('green', f'{self.monitor.total_traffic/1024:.2f}KB'))
        tdelta = timedelta(seconds=time.time() - self.start_time)
        self.average_hits.set_text(
            ('green', f'{self.monitor.total_requests/tdelta.seconds:.2f}'))
        self.event_loop.set_alarm_in(1, self.update_summary)

    def run(self):
        self.event_loop.run()

    def close(self):
        raise urwid.ExitMainLoop()

    def strfdelta(self, tdelta: timedelta, fmt: str) -> str:
        """
        Convert timedelta object into a formatted string.
        Source: https://stackoverflow.com/a/8907269/6050866

        :param tdelta:  timedelta object to be converted.
        :param fmt:     string representation format. e.g:
                        '{days} days and {hours}:{minutes}:{seconds}'

        :return:        formatted string
        """
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)
