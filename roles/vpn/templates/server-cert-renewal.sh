#!/bin/bash

days=60

#Test if certificate expires in the next 60 days
/usr/bin/openssl x509 -checkend $(($days * 24 * 3600)) -in /etc/openvpn/ca/serverCert.pem

if [ $? -eq 1 ]
then
  openssl ca -in /etc/openvpn/ca/serverReq.pem -days 730 -batch -out /etc/openvpn/ca/serverCert.pem -notext -cert /etc/openvpn/ca/caCert.pem -keyfile /etc/openvpn/ca/caKey.pem
  service openvpn-su restart
fi
