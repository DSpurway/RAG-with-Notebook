FROM registry.access.redhat.com/ubi8/python-311

# Set the working directory within the container
WORKDIR /api-flask

# Copy the necessary files and directories into the container
COPY app.py requirements.txt /api-flask/
COPY index.html /api-flask/templates/

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Expose port 8080 for the Flask application
EXPOSE 8080

# Define the command to run the Flask application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "-w", "4", "-t", "300"]
