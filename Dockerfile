# Pull a pre-built alpine docker image with nginx and python3 installed
FROM python:3.11-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive

ENV LISTEN_PORT=8000
EXPOSE 8000

ENV STATIC_URL=/app/contoso_hotel/static

# Set the folder where uwsgi looks for the app
WORKDIR /app

# Copy the app contents to the image
COPY . /app

# ------- START: Installing mssql odbc driver 18 -------
RUN apt-get update ; apt-get install -y  apt-utils curl gpg dialog libterm-readline-gnu-perl libterm-readline-perl-perl ; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg ; \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list ; \
    apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 libgssapi-krb5-2
# ------- END: Installing mssql odbc driver 18 -------

# installing python packages - requirements.txt
COPY requirements.txt /
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir -r /requirements.txt

CMD /app/startup.sh