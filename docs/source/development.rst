.. _base-image:

Development
===========

The current upribox image is based on Raspbian [#Raspbian]_ Stretch
Lite and customized with Ansible (see :ref:`architecture`). The
Raspbian image can be staged into *production* or *development* mode.

Development environment
-----------------------

The following guide assumes that you have a Raspberry Pi with the
upribox image set-up. If you still need help with that task please read
the :ref:`intro` guide. The following guide explains the steps necessary
to setup a development environment for the upribox software.

.. _prerequisities:

Prerequisites [on your development machine]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  install *ansible* 2.3.0 (``sudo pip install ansible==2.3.0``) and
   *git*
-  install requirements for the *ansible* modules (``sudo apt-get install python-pip python-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev``)
-  make sure to log into your Raspberry via SSH once because ansible
   uses ~/.ssh/known\_hosts for verification (or disable host
   verification)
-  add your SSH public key to your Raspberry, e.g. with ``ssh-copy-id```

If you successfully completed the prerequisites you should be able to
login into your upribox via SSH without the need of a password. In
addition you should have *ansible* installed on your computer. Next,
clone the upribox software to your computer:

``git clone https://github.com/usableprivacy/upribox.git``

.. _dev_vs_prod:

Development vs. Production mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The development mode is intended for testing new features and debugging
the upribox software. As such log files are persistent and auto software
updates are disabled. The upribox images available for download are all
set to production mode by default. In production mode log files are
deleted on every reboot and the upribox configuration is automatically
downloaded and updated via github.

.. note::
    The production mode is also intended for the production of purchasable
    pre-assembled boxes. In this process we also create a new user and
    generate a cryptographically secure password. This happens out of scope
    of the production ansible playbook and therefore you have to create a
    user for the web interface on your own when deploying in production mode from scratch.

Development Mode
^^^^^^^^^^^^^^^^

-  copy *environments/development/inventory.sample* to
   *environments/development/inventory*
-  add your RaspberryPi address(es) in the [upriboxes] section in
   environments/development/inventory

Once you added the IP address of your Raspberry Pi to the development
inventory, start changing the upribox source and deploy your local config
with:

``ansible-playbook -i environments/development/inventory site.yml``

Production Mode
~~~~~~~~~~~~~~~

-  copy *environments/production/inventory.sample* to
   *environments/production/inventory*
-  add your Raspberry IP address(es) in the [upriboxes] section in
   *environments/production/inventory*
-  from now on, the config can be deployed with
   ``ansible-playbook -i   environments/production/inventory site.yml``

Creating an image from scratch
------------------------------

If you want to create the entire upribox image from scratch you can use
*setup.yml* ansible playbook. Download the latest Raspian Lite image,
make you sure you have installed all the prerequisites (see :ref:`prerequisities`) and in addition
install *sshpass*.

Set-up the initial upribox base image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  copy *environments/development/inventory.sample* to
   *environments/init/inventory*
-  add your RaspberryPi address(es) in the [upriboxes] section in
   *environments/init/inventory*
-  make sure you have a public/private key pair for ssh on your
   development machine. *~/.ssh/id\_rsa.pub* will be automatically added
   to the authorized\_hosts on the Raspberry
-  run the initial setup with
   ``ansible-playbook -i environments/init/inventory setup.yml`` This
   command will log into your Raspberry with the default credentials
   *pi/raspberry*, create a new user (*upri*) and delete *pi*. Add
   ``--ask-pass`` if you change the default password.
-  from now on, you can deploy the upribox software in
   production or development mode (see :ref:`dev_vs_prod`).
-  after deyploing the upribox software in production mode for the first time,
   you need to create a new webinterface user in */usr/share/nginx/www-upri-interface* on the upribox with
   ``/var/webapp-virtualenv/bin/python manage.py createsuperuser --settings settings_prod``

.. rubric:: Footnotes

.. [#Raspbian] https://www.raspberrypi.org/downloads/raspbian/
