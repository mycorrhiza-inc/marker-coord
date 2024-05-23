FROM python:3.11-bookworm

ENV VIRTUAL_ENV=/usr/local
# use UV
ADD --chmod=755 https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh /install.sh
RUN /install.sh && rm /install.sh
 
WORKDIR /app
COPY . .
 
RUN pip install --no-cache -r requirements.txt 

# expose to docker network
EXPOSE 5000

