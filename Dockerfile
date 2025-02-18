# Use a stable Python version
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker caching
COPY requirements.txt .

# Upgrade pip and install dependencies with longer timeout and fast mirror
RUN pip install --upgrade pip && \
    pip install --default-timeout=100 --no-cache-dir -r requirements.txt --index-url https://pypi.org/simple/

# Ensure the .streamlit directory exists
RUN mkdir -p /root/.streamlit

# Use an ARG for secrets to be passed at build time
ARG STREAMLIT_SECRETS
RUN echo "$STREAMLIT_SECRETS" > /root/.streamlit/secrets.toml

# Copy the rest of the application code
COPY . /app

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "Natpower_Marine_Calculator.py", "--server.port=8501", "--server.address=0.0.0.0"]
