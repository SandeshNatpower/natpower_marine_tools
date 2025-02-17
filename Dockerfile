# Use a stable Python version
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file first to leverage Docker caching
COPY requirements.txt .

# Upgrade pip and install dependencies with longer timeout and fast mirror
RUN pip install --upgrade pip && \
    pip install --default-timeout=100 --no-cache-dir -r requirements.txt --index-url https://pypi.org/simple/

# Copy the rest of the application code
COPY . /app

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
