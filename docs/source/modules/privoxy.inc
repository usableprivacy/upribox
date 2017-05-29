privoxy
-------

This role deploys the Privoxy [#Privoxy]_ filter proxy on the upribox. The upribox uses Privoxy to: filter unwanted content in HTTP requests
such as advertisement or tracker code. In addition to content filtering, Privoxy injects a custom CSS file into websites to stop
(filtered) ads from showing up in websites. The filter configuration for Privoxy is stored in `/etc/privoxy` and updated periodically.
