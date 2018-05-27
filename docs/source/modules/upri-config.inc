upri-config
-----------

The *upri-config* role deploys the upri-config script, which is used for configuring the upribox.
Additionally necessary cron jobs for updates and other tasks are copied.
The main parts of this role are the following:

- deployment of the upri-config script

 - create virtualenv
 - copy upri-config files
 - link managament script

- The upribox updates every hour to the latest version on github via ansible.
  For this purpose the common role needs to execute among others the following tasks before updating:

 - configuring cron jobs

  - update the upribox
  - update the filter rules
  - parse user-agents which are used to fingerprint the devices connected to the upribox
  - parse log files used for statistics
