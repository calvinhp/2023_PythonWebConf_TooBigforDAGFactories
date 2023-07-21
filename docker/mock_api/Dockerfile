# Sets the base image for subsequent instructions
#FROM ubuntu:23.10
#FROM python:3-alpine
FROM python:3.12.0b3-bullseye
#FROM python:3.8-slim-buster

# Sets the working directory in the container
WORKDIR /app
RUN apt-get update -y
#RUN apt-get install -y python3-pip
#python-dev

# Copies the dependency files to the working directory
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copies everything to the working directory
COPY app.py /app/app.py

# Command to run on container start
EXPOSE 5000
#ENTRYPOINT ["python"]
CMD [ "python" , "./app.py", "--host","0.0.0.0", "--port", "5000"]
