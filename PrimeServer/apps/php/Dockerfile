FROM php:8.3-fpm-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libzip-dev libsqlite3-dev unzip git \
    && docker-php-ext-install pdo_mysql pdo_sqlite zip \
    && rm -rf /var/lib/apt/lists/*
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /var/www/html
