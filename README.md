# HTTP log monitoring console program

## Usage

Usage:

```shell
pipenv run python logmon [-h] [-f FILE_PATH] [-r REFRESH_RATE] [-d ALERT_DURATION] [-t ALERT_THRESHOLD]
```

Where:

- `-f`, `--file-path`: File path of the log file.
- `-r`, `--refresh-rate`: Refresh rate for the sections (in seconds).
- `-d`, `--alert-duration`: Duration for alerting (in seconds).
- `-t`, `--alert-threshold`: Threshold for average requests (per second) over the alert duration.

### Manual

- Requires Python 3.7+.
- Dependency management with `Pipenv` - Install pipenv: `pip install pipenv && pipenv install`
- Install dependencies - `pipenv install`
- Launch with pipenv - `pipenv run python -m logmon [args]`

**NOTE**: The log file must already exist.

### Docker

- Build: `docker build . -t ddog-log-mon`
- Run: ``docker run a STDIN -a STDOUT -i -t -v `pwd`/log:/var/log ddog-log-mon``

**NOTE**: You'll need to ensure the `./log` folder contains an `access.log` file.

## Tests

Run tests using the following command:

- `pipenv run python -m unittest test.test_alert`

## Potential Improvements

- Make the file monitor async with a callback function, instead of using an urwid event loop alarm. Could probably use the watchdog library for this.
- Track additional statistics such as status codes (especially 5xx), method (GET, POST, etc), user, and user-agent.
- Create additional alert types, such as when 5xx errors are over a certain threshold.
- Add graphs of traffic (in KBs) and number of requests (per second).
- Add additional logging.
- Support different log file types.
- Make the monitor more independant and implement a collections server. This would allow us to monitor remote systems.

## Requirements

Consume an actively written-to w3c-formatted HTTP access log [(https://en.wikipedia.org/wiki/Common_Log_Format)](https://en.wikipedia.org/wiki/Common_Log_Format). It should default to reading /var/log/access.log and be overridable.

Example log lines:

```plaintext
127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 1234

127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 1234

127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234

127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234
```

- Display stats every 10s about the traffic during those 10s: the sections of the web site with the most hits, as well as interesting summary statistics on the traffic as a whole. A section is defined as being what's before the second '/' in the path. For example, the section for `http://my.site.com/pages/create` is `http://my.site.com/pages`.
- Make sure a user can keep the app running and monitor the log file continuously
- Whenever total traffic for the past 2 minutes exceeds a certain number on average, add a message saying that `High traffic generated an alert - hits = {value}, triggered at {time}`. The default threshold should be 10 requests per second and should be overridable.
- Whenever the total traffic drops again below that value on average for the past 2 minutes, print or displays another message detailing when the alert recovered.
- Write a test for the alerting logic.
- Explain how you’d improve on this application design.
- If you have access to a linux docker environment, we'd love to be able to docker build and run your project! If you don't though, don't sweat it. As an example:

```dockerfile
FROM python:3

RUN touch /var/log/access.log # since the program will read this by default

WORKDIR /usr/src

ADD . /usr/src

ENTRYPOINT ["python", "main.py"]
```