import re
from logging import getLogger
from os import SEEK_END
from datetime import datetime
from dataclasses import dataclass

_logger = getLogger(__name__)


@dataclass
class LogItem:
    time: datetime
    section: str
    size: int
    status: int

    @staticmethod
    def parse_line(line: str):
        """
        Source: https://gist.github.com/sumeetpareek/9644255
        Parse the log line and return a LogItem.

        :param line:    string in the form of a common log format line.

        :return:        LogItem(time, section, size, status)
        """
        parts = [
            r'(?P<host>\S+)',       # host %h
            r'\S+',                 # indent %l (unused)
            r'(?P<user>\S+)',       # user %u
            r'\[(?P<time>.+)\]',    # time %t
            r'"(?P<request>.*)"',   # request "%r"
            r'(?P<status>[0-9]+)',  # status %>s
            r'(?P<size>\S+)',       # size %b (careful, can be '-')
            r'"(?P<referrer>.*)"',  # referrer "%{Referer}i"
            r'"(?P<agent>.*)"',     # user agent "%{User-agent}i"
        ]
        pattern = re.compile(r'\s+'.join(parts)+r'\s*\Z')

        data: dict = {}
        match = pattern.match(line)
        if match is not None:
            data = match.groupdict()

        return LogItem(
            # '%d-%m-%Y %H:%M:%S %z' = dd/mm/yyyy hh:mm:ss timezone
            datetime.strptime(data['time'], '%d/%b/%Y:%H:%M:%S %z'),
            data['request'].split(' ')[1].split('/')[1],
            int(data['size']),
            int(data['status']))


class LogTailer:

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.file = open(file_path, 'r')
        self.file.seek(0, SEEK_END)

    def get_new_lines(self) -> list:
        lines = self.file.readlines()
        return [line.strip() for line in lines]
