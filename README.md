# Foodgram —  Продуктовый помощник.
Онлайн-сервис с соответствующим API. Пользователи могут публиковать рецепты, подписываться на других пользователей, добавлять любимые рецепты в список «Избранное» и загружать список продуктов в магазин для приготовления выбранных блюд.
Проект основан на Django и DjangoRestFramework, и доступ к данным осуществляется через API.


### Описание проекта
- Пользователи могут регистрироваться.
- Загружать фотографии с описанием.
- Смотреть питомцев других пользователей.


### Технологии
- Python
- Django
- djangorestframework
- PostgreSQL
- React
- Doker
- Nginx
- Gunicorn
- CI/CD


### Установка - Все примеры указаны для Linux

1. Склонируйте репозиторий на свой компьютер:
    ```
    git clone git@github.com:Kirill-kuz/foodgram-project-react.git
    ```
2. Создайте файл .env и заполните его своими данными.
    ```
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=mysecretpassword
    POSTGRES_DB=django
    DB_HOST=db
    DB_PORT=5432
    SECRET_KEY_DJANGO=ключ от джанго - KEY_DJANGO 
    SECRET_DEBUG=False / True (выберите одно нужное значение)
    SECRET_ALLOWED_HOSTS=ip и/или домен
    ```

### Создание Docker-образов и загрузка их в DockerHub

1. Замените `YOUR_USERNAME` на свой логин на DockerHub:

    ```
    cd frontend
    docker build -t YOUR_USERNAME/foodgram_frontend .
    cd ../backend
    docker build -t YOUR_USERNAME/foodgram_backend .
    cd ../nginx
    docker build -t YOUR_USERNAME/foodgram_gateway . 
    ```

2. Загрузите образы на DockerHub:
    Можно вополнить одной командой или поочередно, но нужно удалить '&&'
    ```
    docker push YOUR_USERNAME/foodgram_frontend &&
    docker push YOUR_USERNAME/foodgram_backend &&
    docker push YOUR_USERNAME/foodgram_gateway
    ```

### Деплой на сервер

1. Подключитесь к удаленному серверу

2. Создайте на сервере директорию `foodgram`:

    ```
    mkdir foodgram
    ```

3. Установите Docker Compose на сервер:

    ```
    sudo apt update
    sudo apt install curl
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo apt install docker-compose
    ```

4. Скопируйте файлы `docker-compose.production.yml` и `.env` в директорию `foodgram/` на сервере:

    ```
    scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME docker-compose.production.yml YOUR_USERNAME@SERVER_IP_ADDRESS:/home/YOUR_USERNAME/foodgram/docker-compose.production.yml
    ```
        
    Где:
    - `PATH_TO_SSH_KEY` - путь к файлу с вашим SSH-ключом
    - `SSH_KEY_NAME` - имя файла с вашим SSH-ключом
    - `YOUR_USERNAME` - ваше имя пользователя на сервере
    - `SERVER_IP_ADDRESS` - IP-адрес вашего сервера


    или создайте файлы вручную и скопируйте в них информацию 
    ```
    sudo nano .env
    вставляем информацию из .env
    ctrl+O (сохранить) 
    ctrl+X (выйти)

    sudo nano docker-compose.production.yml
    вставляем информацию из docker-compose.production.yml
    ctrl+O (сохранить) 
    ctr+X (выйти)
    ```
    Проверяем что файлы есть, вводим в командной строке
    ```
    ls -la
    ```
    Видим 2 созданных нами файла

5. Запустите Docker Compose в режиме демона:

    ```
    sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml up -d
    ```

6. Выполните миграции, соберите статические файлы бэкенда и скопируйте их в `/backend_static/static/`:

    ```
    sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py migrate
    sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend cp -r /app/static/. /static/
    ```

7. Откройте конфигурационный файл Nginx в редакторе nano:

    ```
    sudo nano /etc/nginx/sites-enabled/default
    ```

8. Измените настройки `location` в секции `server`:

    ```
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:9080;
    }
    ```

9. Проверьте правильность конфигурации Nginx:

    ```
    sudo nginx -t
    ```

    Если вы получаете следующий ответ, значит, ошибок нет:

    ```
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```

10. Перезапустите Nginx:

    ```
    sudo systemctl restart nginx
    ```

### Настройка CI/CD

1. Файл workflow уже написан и находится в директории:

    ```
    foodgram/.github/workflows/main.yml
    ```

2. Для адаптации его к вашему серверу добавьте секреты в GitHub Actions:

    ```
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    HOST                           # IP-адрес сервера
    USER                           # имя пользователя
    SSH_KEY                        # содержимое приватного SSH-ключа (cat ~/.ssh/id_rsa)
    SSH_PASSPHRASE                 # пароль для SSH-ключа
    TELEGRAM_TO                    # ID вашего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
    TELEGRAM_TOKEN                 # токен вашего бота (получить токен можно у @BotFather, команда /token, имя бота)
    ```

