#!/bin/bash
sleep 10
mongosh -u admin -p password --authenticationDatabase admin --host mongo:27017 /etc/init-mongo.js