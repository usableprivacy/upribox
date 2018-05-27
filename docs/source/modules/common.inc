common
------

The *common* role lays the groundwork for the following more specific roles. The main parts of this role are the following:

- installation of required software

- building the infrastructure for logging

 - creating the logging directory (``/var/tmp/log`` for production and ``/var/log/log`` for development mode, see :ref:`dev_vs_prod`)
 - updating rsyslog config and deleting old rsyslog logfiles
 - configuring logrotate

- settings and configurations

 - writing default settings
 - copying ansible config
 - creating directory for local facts (see :ref:`customization`)

- In order to be able to update the upribox, following task are necessary:

 - installing ansible
 - copying the update script
 - copying git deployment key

- deploying the upribox recovery mechanism

 - restarts update at system boot if the update was interrupted
