FROM python:3.11-slim
WORKDIR /app

# Install dependencies and Rust
RUN apt-get update && apt-get install -y curl \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y

# Update PATH to include Cargo
ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 6543

CMD [ "python","-m","flask_route" ]
