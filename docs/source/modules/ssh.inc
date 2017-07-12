ssh
---

By default the upribox can be reached via SSH. This feature can be disabled in the admin page of the web interface or
directly by calling the *enable_ssh* action of the configuration script *upri-config.py* (see :ref:`django-label`).

.. note::
    In the web interface it is not possible to deactivate WiFi (Silent and Ninja), SSH and Apate, since this scenario
    would make the upribox unreachable. Therefore one of the services should always be up and running. (see :ref:`integration`)
