FROM alpine:latest



# Set working directory
WORKDIR /app
ENV HOME /app

COPY requirements.txt /app

# Update and install packages
RUN apk update

RUN apk add python3 py3-pip

# Install requirements (assuming they don't include SQLite)
RUN pip3 install -r requirements.txt
RUN pip3 install sqlite3  

# Define volume mount point for database (modify path as needed)
VOLUME ["/app/database.db"]

# Copy application code and empty database init script (modify paths)
COPY campusapptools /app
COPY client_api_sqllite.py /app
#COPY source/update_log.json /app
#COPY campusapptools/build_db.py /app

# Initialize database schema 
RUN python3 campusapptools/build_db.py  

# Create a non-root user and set file permissions
RUN addgroup -S app \
    && adduser -S -g app -u 1000 app \
    && chown -R app:app /app

# Run as the non-root user
USER 1000

# Entrypoint command
ENTRYPOINT ["python3", "client_api.py"]
CMD ["--port", "8080"]
