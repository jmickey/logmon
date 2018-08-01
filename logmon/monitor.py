from datetime import datetime, timezone
from logging import getLogger
from .log_utils import LogTailer, LogItem
from .alert import TrafficAlert

_logger = getLogger(__name__)


class HTTPLogMonitor:

    def __init__(
            self, file_path: str = None, alert_duration: int = 120,
            alert_threshold: int = 10, refresh_rate: float = 10.0) -> None:
        self.file_path = file_path
        self.alert_duration = alert_duration
        self.alert_threshold = alert_threshold
        self.alert_traffic = self.alert_duration * self.alert_threshold
        self.refresh_rate = refresh_rate
        if self.file_path is not None:
            self.log_tailer = LogTailer(self.file_path)
        self.total_requests = 0
        self.total_traffic = 0
        self.alert = None
        self.log_data: list = []
        self.short_log_data: list = []

    def update(self):
        """
        Retreives new log lines, parses them, and stores them in memory
        """
        self.remove_old_logs()
        lines = self.log_tailer.get_new_lines()
        if lines:
            for line in lines:
                log_item = LogItem.parse_line(line)
                self.log_data.append(log_item)
                self.short_log_data.append(log_item)
                self.total_traffic += log_item.size
                self.total_requests += 1
        self.update_alert_status()

    def remove_old_logs(self):
        """
        Remove logs from the short and long term log data lists based
        on the refresh rate and alert duration respectively.
        """
        now = datetime.now(timezone.utc)
        self.log_data = [ln for ln in self.log_data
                         if (now - ln.time).seconds < self.alert_duration]
        self.short_log_data = [ln for ln in self.short_log_data
                               if (now - ln.time).seconds < self.refresh_rate]

    def update_alert_status(self):
        """
        Check alert status based on alert duration and threshold.

        Alerts are triggered if the average number of requests per second
        is larger than the alert threshold, over the alert duration.

        Therefore, it is simply a case of ensuring the length of the log_data
        list is not larger than the alert_threshold * alert_duration.
        """
        hits = len(self.log_data)
        if hits > self.alert_traffic and not self.alert:
            self.alert = TrafficAlert(time_recovered=None, hits=hits)
            _logger.info(self.alert)
        elif (hits < self.alert_traffic
              and self.alert is not None
              and not self.alert.recovered):
            self.alert.recover()
            _logger.info(self.alert)
        elif self.alert and self.alert.recovered:
            self.alert = None
