privoxy
-------
This role deploys the Privoxy_ filter proxy on the upribox. The upribox uses Privoxy_ to: filter unwanted content in HTTP requests
such as advertisement or tracker code. In addition to content filtering, Privoxy_ injects a custom CSS file into websites to stop
(filtered) ads from showing up in websites. The filter configuration for Privoxy_ is stored in `/etc/privoxy` and updated periodically.
