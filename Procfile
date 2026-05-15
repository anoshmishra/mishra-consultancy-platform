web1: gunicorn djangoProject.wsgi --log-file -
worker: celery -A djangoProject worker --loglevel=info --pool=solo
