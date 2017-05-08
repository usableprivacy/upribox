common
------

The *common* role lays the groundwork for the following more specific roles. The main parts of this role are the following:

- building the infrastructure for logging

 - creating the logging directory (``/var/tmp/log`` for production and ``/var/log/log`` for development mode, see :ref:`dev_vs_prod-label`)
 - updating rsyslog config and deleting old rsyslog logfiles
 - configuring logrotate

- settings and configurations

 - writing default settings
 - copying ansible config
 - creating directory for local facts (see :ref:`customization`)

- The upribox updates every 4 hours to the latest version on github via ansible. For this purpose the common role needs to execute among others the following tasks before updating

 - installing ansible
 - configuring a cron job
 - copying the update script
 - copying git deployment key

- update of the filter rules
- creating crontab entry to parse user-agents which are used to fingerprint the devices connected to the upribox
