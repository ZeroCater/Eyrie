release: python manage.py migrate
web: gunicorn eyrie.wsgi --log-file - --reload
worker: python manage.py rqworker
