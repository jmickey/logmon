import unittest
import time
from datetime import datetime, timezone
from logmon.monitor import HTTPLogMonitor
from logmon.log_utils import LogItem


class TestAlertLogic(unittest.TestCase):

    log_lines = [LogItem(datetime.now(timezone.utc), 'section1', 0, 0)
                 for _ in range(1210)]

    def test_alert_triggered(self):
        mon = HTTPLogMonitor()
        mon.log_data = self.log_lines
        mon.update_alert_status()
        self.assertIsNotNone(mon.alert)
        self.assertEqual(mon.alert.recovered, False)

    def test_alert_duration(self):
        mon = HTTPLogMonitor(alert_duration=1)
        mon.log_data = self.log_lines
        mon.update_alert_status()
        time.sleep(2)
        mon.remove_old_logs()
        mon.update_alert_status()
        self.assertIsNotNone(mon.alert)
        self.assertEqual(mon.alert.recovered, True)


if __name__ == '__main__':
    unittest.main()
