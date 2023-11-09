# Change Log
All notable changes to this project will be documented in this file.

## [0.2.1] - 2023-11-06
**Fixed bugs:**
- The same content was written several times in the alive message 


## [0.2.0] - 2023-11-03
**Implemented enhancements:**
- Added mechanism to handle more channels of notifications
- Added email channel notification
- Added mechanism for optimizing the output message


## [0.1.5] - 2023-10-29
**Implemented enhancements:**
- In the alive message added the name of the cluster and the time without warning/alarm
- In pods filters, added the status "ContainerCreating" to the OK


## [0.1.4] - 2023-10-28
**Implemented enhancements:**
- The response from http request (telegram api call)  is limited to 10 characters
- In pod message details add the container status

**Fixed bugs:**
- The pod in "Succeeded" state is not considered a critical state  

## [0.1.3] - 2023-10-25

**Implemented enhancements:**
- add a new key in .env file to define the cluster name. When the script runs in the k8s, get cluster name does not work 
- optimized source code in file main.py 
- add version.py to store the version of script. It is aligned to the CHANGELOG.md latest version

## [0.1.2] - 2023-10-23
 
**Implemented enhancements:**
- add Jenkins pipeline for building the docker image and push it to the hub registry 

## [0.1.1] - 2023-10-21
 
**Implemented enhancements:**
- add cluster name in the message details

**Fixed bugs:**
- during the loading of .env keys, the system printed wrong default value

## [0.1.0] - 2023-10-20
 
### First Commit

v0.1.0: [https://github.com/seriohub/k8s-watchdog/releases/tag/v0.1.0](https://github.com/seriohub/k8s-watchdog/releases/tag/v0.1.0)