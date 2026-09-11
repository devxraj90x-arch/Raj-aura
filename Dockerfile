FROM php:8.3-apache
RUN apt-get update && apt-get install -y python3 python3-pip libsqlite3-dev && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install pdo_sqlite
WORKDIR /var/www/html
COPY . /var/www/html/
RUN pip3 install --no-cache-dir -r requirements.txt
RUN chmod -R 777 /var/www/html
CMD bash -c 'python3 /var/www/html/app.py & apache2-foreground'
