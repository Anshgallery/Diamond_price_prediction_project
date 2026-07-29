# A Dockerfile is a text file containing a *set of instructions* used to build a Docker image for an application. The Docker image packages the application code, dependencies, libraries, runtime, and configuration needed to run the application consistently in any environment.
# Think of Docker Hub as an online storage/library for Docker Images.

FROM python:3.9-slim-buster 
#"Go to Docker Hub, find the python image with the 3.9-slim-buster tag, and use it as the base image for my application."

#Different containers are separated from each other, so one container's application, dependencies, or processes do not directly interfere with another container.

WORKDIR /service
COPY . ./
RUN pip install -r requirements.txt
ENTRYPOINT ["python3","app.py"]


