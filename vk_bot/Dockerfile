FROM python:3.11

COPY requirements.txt .
RUN pip install --user -r requirements.txt

WORKDIR /code

COPY .. .

ENV PYTHONPATH = "$PYTHONPATH:/code"
CMD ["python", "-u", "vk_bot/main.py"]
