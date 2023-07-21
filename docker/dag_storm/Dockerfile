FROM python:3.12.0b3-bullseye

# Sets the working directory in the container
WORKDIR /app
RUN apt-get update -y

COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copies everything to the working directory
COPY dag_storm.py /app/dag_storm.py

#ENTRYPOINT ["python"]
#CMD [ "./dag_storm.py" ]
