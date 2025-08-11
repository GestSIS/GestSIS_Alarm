FROM python:3.13.5

RUN apt-get update && apt-get install -y --no-install-recommends default-libmysqlclient-dev build-essential
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

CMD ["sh"]
