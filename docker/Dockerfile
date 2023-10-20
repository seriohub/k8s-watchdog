FROM python:3.10 as k8s-watchdog
LABEL mantainer="LS"
# ARG DEBIAN_FRONTEND=noninteractive

# Update packages and install basics
RUN apt-get update && apt-get install -y \
	wget \
	unzip \
	git \
	nano

RUN apt-get -y install python3-pip

RUN pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# prepare dir
RUN mkdir /app
# Set the working directory inside the container
WORKDIR /app

# Copy the project files to the container
COPY /src /app

# Exclude specific files or directories from the project
# Add more `--exclude` arguments as needed
RUN find . -type f -name "tmp" -exec rm -rf {} +
RUN find . -type f -name "*.yaml" -exec rm -f {} +
RUN find . -type f -name "__pycache__" -exec rm -f {} +
RUN find . -type f -name "*.env" -exec rm -f {} +

RUN rm -rf /app/tmp /app/__pycache__
# create an empty logs folder
RUN mkdir /logs

# create an empty config folder
RUN mkdir /config

# Expose a volume for external access
VOLUME /app/logs

WORKDIR /app/
RUN echo "Ready!"
CMD ["python3","-u" , "main.py"]
