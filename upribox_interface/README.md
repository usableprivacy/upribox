upribox Django web interface
------------------------

### Development instructions:

- Requires Python 2.7
- Local Redis Server (port 6379) is required
- use of *virtualenv* is recommended

   ```bash
   virtualenv ~/upri-virtualenv # Pfad kann beliebig gewählt werden
   source ~/upri-virtualenv/bin/activate
   ```
- Install dependencies

   ```bash
   cd upribox_interface
   pip install -r requirements.txt
   ```
- Create database

   ```bash
   python manage.py migrate --settings settings_dev
   ```
- Create test user (upri/upri)

   ```bash
   python manage.py loaddata dev_user --settings settings_dev
   ```
- Create worker for processing tasks

This creates a process that receives tasks from the Django task queue. The worker process runs in the foreground until terminated with CTRL+C. *Important: If no worker process is running all webinterface actions (e.g. configure WiFi, starting Tor) are not processed.*

   ```bash
   python manage.py rqworker --settings settings_dev
   ```
- Start the webinterface

   ```bash
   python manage.py runserver --settings settings_dev
   ```

### Translation
-------------

Command to create the English language files:

 ```bash
 python manage.py makemessages -l en --settings=settings_prod -e html,py -i settings_prod.py -i urls.py -i settings_dev.py -i manage.py -i wsgi.py -i middleware
 ```

 -------------------------------------------------------------------------------------------

 The translation is then done in every local translation folder for earch of the Django apps. (*django.po* files)

 -------------------------------------------------------------------------------------------

Once the translation has been completed, the localization files have to be compiled. The following command has to be executed for each of the Django apps.
```bash
 django-admin compilemessages [-l en]
  ```
