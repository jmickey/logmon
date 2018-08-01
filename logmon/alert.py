from logging import getLogger
from datetime import datetime
from dataclasses import dataclass

_logger = getLogger(__name__)


@dataclass
class BaseAlert:
    time_recovered: datetime
    time_triggered: datetime = datetime.now()
    recovered: bool = False

    def __str__(self):
        if self.recovered:
            return ('Generic alert recovered at '
                    f'{self.time_recovered:%d-%m-%Y %I:%M%p}')
        return ('Generic alert triggered at '
                f'{self.time_triggered:%d-%m-%Y %I:%M%p}')

    def recover(self):
        self.recovered = True
        self.time_recovered = datetime.now()


@dataclass
class TrafficAlert(BaseAlert):
    hits: int = 0

    def __str__(self):
        if self.recovered:
            return ('High traffic alert recovered at '
                    f'{self.time_recovered:%d-%m-%Y %I:%M%p}')
        return (f'High traffic generated an alert - hits = {self.hits}, '
                f'triggered at {self.time_triggered:%d-%m-%Y %I:%M%p}')
