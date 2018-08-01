FROM python:3.7
RUN pip install pipenv
RUN touch /var/log/access.log

WORKDIR /usr/src/logmon
COPY Pipfile* ./

RUN pipenv install --system --deploy

COPY ./logmon ./logmon

ENTRYPOINT [ "python", "-m", "logmon", "-f", "/var/log/access.log" ]