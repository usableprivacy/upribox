.. _django-label:

django
------

The upribox user interface (see :ref:`web_interface`) is based on the Python Web framework Django [#Django]_.
The role is responsible for installing the requirements to a virtual environment, copying the web interface files,
setting up the database and installing services like a supervisor (for the rqworker) and the application container uWSGI.
By deploying this role the upribox also starts a cleanup process for the saved statistic files removing data older than 6 months.

.. note::
    For privacy reasons the upribox does not keep the ad-blocking logfile with timestamps and URLs but tries to aggregate
    the information as soon as possible to store only the information that is needed for the statistics and to assure
    anonymity. (see :ref:`logs`)
