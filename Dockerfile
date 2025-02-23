FROM python:3

# Set the working directory
WORKDIR /usr/app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD python3 main.py