FROM python:3.12.5-bookworm
WORKDIR /github_engagements_backend
COPY ./requirements.txt /github_engagements_backend
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host", "0.0.0.0"]