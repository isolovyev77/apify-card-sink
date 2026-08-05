# Light image: this Actor never opens a store page, it only needs an MCP client and HTTP.
FROM apify/actor-python:3.12

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD ["python", "-m", "src.main"]
