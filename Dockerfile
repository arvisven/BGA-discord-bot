FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV DISCORD_TOKEN=apa
ENV NOTIFY_CHANNEL_ID=boll

# Run script.py when the container launches
CMD ["python", "script.py"]
