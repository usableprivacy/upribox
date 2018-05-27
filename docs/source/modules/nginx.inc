nginx
-----
This role is used to install and set-up nginx for the upribox. The nginx web server is responsible for a number of tasks:

upribox blackhole
^^^^^^^^^^^^^^^^^
The blackhole setup returns an empty response for any request it receives, depending on the type of request this could be
either an empty HTML page, or a blank image file. The server in addition attempts to reset/delete browser cookies for
filtered domains: for every cookie the server receives, the server responds with the same cookie with empty values and a validity of 0.
This setup ensures that tracking cookies are deleted from the user's browser the moment the request for a domain filtered by the upribox is made.

upribox CSS filter
^^^^^^^^^^^^^^^^^^
The upribox serves custom CSS files to remove ad-content from websites. The custom domain to serve CSS files is: *filter.upri.box*.
CSS filters are loaded from `/etc/nginx/lua/css.lua` and periodically updated.

upribox web interface
^^^^^^^^^^^^^^^^^^^^^
The nginx role finally prepares the setup for the upribox web interface. The nginx configuration ensures that requests to
following URLs are forwarded to the upribox Django web interface.

- `http://upri.box <http://upri.box/>`_
- `https://upri.box:4300 <https://upri.box:4300/>`_
- `http://upribox.local <http://upribox.local/>`_
- `https://upribox.local:4300 <https://upribox.local:4300/>`_
