# Base image
FROM alpine:latest

# Working directory
WORKDIR /app

# Copy application code
COPY requirements.txt /app
COPY campusapptools/ /app/campusapptools
COPY client/ /app/client
COPY client_api_sqllite.py /app
COPY data/ /data

# Update and install packages
RUN apk update

RUN apk add -U python3
RUN apk add --update py3-pip
#RUN mv /app/source/requirements.txt /app/requirements.txt
RUN pip3 install --upgrade pip --break-system-packages
RUN pip3 install --upgrade setuptools --break-system-packages
#RUN pip3 install -U setuptools
RUN pip3 install -r requirements.txt --break-system-packages


# Delete any conflicting file (if necessary)
#RUN rm -f /data/spaces.db

# Define volume mount point for database
VOLUME ["/data"]

# Create an empty spaces.db file within the container (optional)
# This step is optional and depends on your approach.
# Create the /data directory
#RUN mkdir -p /data
# RUN touch /data/spaces.db

# Initialize database schema 
#RUN python3 campusapptools/build_db.py  

# Create a non-root user and set file permissions
RUN addgroup -S app \
  && adduser -S -g app -u 1000 app \
  && chown -R app:app /app

# Run as the non-root user
USER 1000

# Entrypoint command
CMD ["python3", "-m", "flask", "--app", "/app/client_api_sqllite.py", "run", "--host", "0.0.0.0", "--port", "8080"]
