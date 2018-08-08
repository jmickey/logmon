import logging
import os
import argparse
from .display import Display
from .monitor import HTTPLogMonitor


def main():
    dir_path = '/usr/log/logmon.log'

    # Store application logs in project directory during development
    if 'ENV' in os.environ and os.environ['ENV'].lower() == 'development':
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        dir_path = f'{curr_dir}/../logs/logmon.log'

    # Initialise the logging config.
    try:
        logging.basicConfig(
            filename=f'{dir_path}', level=logging.INFO)
    except FileNotFoundError as e:
        os.makedirs(os.path.dirname(dir_path))
        logging.basicConfig(
            filename=f'{dir_path}', level=logging.INFO)

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--file-path', default='/var/log/access.log',
        help="File path of the log file.")
    parser.add_argument(
        '-r', '--refresh-rate', default=10, type=float,
        help="Refresh rate for the sections (in seconds).")
    parser.add_argument(
        '-d', '--alert-duration',
        default=120, type=int, help="Duration for alerting (in seconds).")
    parser.add_argument(
        '-t', '--alert-threshold', default=10, type=int,
        help='Threshold for average requests per second over the alert '
             'duration.')
    args = parser.parse_args()

    file_path = args.file_path
    refresh_rate = args.refresh_rate
    alert_duration = args.alert_duration
    alert_threshold = args.alert_threshold

    monitor = HTTPLogMonitor(
        file_path, alert_duration, alert_threshold, refresh_rate)

    display = Display(monitor, refresh_rate)
    display.run()


if __name__ == "__main__":
    main()
