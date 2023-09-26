FROM python:3.11-slim-buster

# Set the working directory to /pytket-phir
WORKDIR /pytket-phir

# Copy the pyproject.toml and requirements.txt files to the container
COPY . .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the web server
CMD ["python", "-m", "pytket.phir.main"]
