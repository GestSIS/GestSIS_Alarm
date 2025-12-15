FROM python:3.13.5

RUN apt-get update && apt-get install -y --no-install-recommends default-libmysqlclient-dev build-essential
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install uv
WORKDIR /app

CMD ["sh"]
