# K8s-Watchdog

> [!WARNING]  
**Attention Users:** This project is in active development, and certain tools or features might still be under construction. We kindly urge you to exercise caution while utilizing the tools within this environment. While every effort is being made to ensure the stability and reliability of the project, there could be unexpected behaviors or limited functionalities in some areas.
We highly recommend thoroughly testing the project in non-production or sandbox environments before implementing it in critical or production systems. Your feedback is invaluable to us; if you encounter any issues or have suggestions for improvement, please feel free to [report them](https://github.com/seriohub/velero-watchdog/issues). Your input helps us enhance the project's performance and user experience.
Thank you for your understanding and cooperation.

## Description

This project is designed for monitoring the health of Kubernetes environment and alert when something is not working.
The scope is to check if the status of the elements are  in ready, running, bound state or if the amount of pods requested is always satisfied. 
Property such as CPU or memory usage are not checked to trigger an alarm.

The user chooses the synchronization timer and which elements to monitor.

## Features

### 1. Monitoring nodes status

Monitor both masters and works nodes.

### 2. Monitoring Pods and Workload

Monitor the status of :

- Pod
- Deployments
- StatefulSets
- DaemonSet
- ReplicaSet

### 3. Monitor Persistent Volume and  Persistent Volume Claim

Monitor the status of :

- Persistent Volume
- Persistent Volume Claim  

### 4. Telegram Integration

Receive the alert and the solved message via Telegram, allowing immediate action.

## Requirements

- Python 3.x
- kubectl cli (if [Run in kubernetes](#run-in-kubernetes))
- Telegram API credentials

## Configuration

| FIELD                       | TYPE   | DEFAULT | DESCRIPTION                                                                                                                                               |
|-----------------------------|--------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DEBUG`                     | Bool   | False   | View debugging information.                                                                                                                               |
| `LOG_SAVE`                  | Bool   | False   | Save log to files                                                                                                                                         |
| `PROCESS_LOAD_KUBE_CONFIG`* | Bool   | True    | Set False if it runs on k8s.                                                                                                                              |
| `PROCESS_KUBE_CONFIG`       | String |         | Path to the kube config file. This is mandatory when the script runs outside the Kubernetes cluster, either in a docker container or as a native script.  |
| `PROCESS_CYCLE_SEC`         | Int    | 120     | Cycle time (seconds)                                                                                                                                      |
| `TELEGRAM_ENABLE`    *      | Bool   | True    | Enable sending messages                                                                                                                                   |
| `TELEGRAM_API_TOKEN` *      | String |         | Token for access to Telegram bot via Http API                                                                                                             |
| `TELEGRAM_CHAT_ID`   *      | String |         | Telegram chat id where send the notifications                                                                                                             |
| `K8S_NODE`                  | Bool   | True    | Enable Nodes watcher                                                                                                                                      |
| `K8S_PODS`                  | Bool   | True    | Enable Pods watcher                                                                                                                                       |
| `K8S_DEPLOYMENT`            | Bool   | True    | Enable Deployment watcher                                                                                                                                 |
| `K8S_STATEFUL_SETS`         | Bool   | True    | Enable StatefulSets watcher                                                                                                                               |
| `K8S_REPLICA_SETS`          | Bool   | True    | Enable ReplicaSets watcher                                                                                                                                |
| `K8S_DAEMON_SETS`           | Bool   | True    | Enable DaemonSet watcher                                                                                                                                  |
| `K8S_PVC`                   | Bool   | True    | Enable Persistent Volume Claim watcher                                                                                                                    |
| `K8S_PV`                    | Bool   | True    | Enable Persistent Volume watcher                                                                                                                          |
| `K8S_DEPLOYMENT_P0`         | Bool   | False   | Load the Deployment items where the pods count is 0                                                                                                       |
| `K8S_STATEFUL_SETS_P0`      | Bool   | False   | Load the StatefulSets items where the pod count is 0                                                                                                      |
| `K8S_REPLICA_SETS_P0`       | Bool   | False   | Load the ReplicaSets items where the pod count is 0                                                                                                       |
| `K8S_DAEMON_SETS_P0`        | Bool   | False   | Load DaemonSet items where the pods count is scaled to 0 or is equal to 0                                                                                 |

*Mandatory parameters

If you set "TELEGRAM_ENABLE"= False, the application print the message on the stdout

## Installation

Clone the repository:

  ``` bash
    git clone https://github.com/seriohub/k8s-watchdog.git
    cd k8s-watchdog
  ```

### Run native

1. Navigate to the [src](src) folder

2. Dependencies installation:

    ``` bash
    pip install -r requirements.txt
    ```

3. Configuration

    Create and edit .env file under src folder, you can start from [.env.template](src/.env.template) under [src](src) folder
    Setup mandatory parameters in the src/.env file if runs it in the native mode

4. Usage

    Run the main script:

    ``` bash
    python3 main.py
    ```

### Run in Docker

1. Configuration
   1. Navigate to the [docker](docker) folder
   2. Setup mandatory parameters in the docker-compose.yaml file ([docker-compose.yaml](docker/docker-compose.yaml))

      **Note:** Instead of editing the docker-compose.yaml file, you can create and edit .env file (you can start from [.env.template](docker/.env.template)) file under [docker](docker) folder and use the docker-compose.yaml default  values.
2. Docker image :
   ##### Build docker image from scratch
      1. Navigate to the root folder
      2. Build the docker image
      ``` bash
      docker build --target k8s-watchdog -t k8s-watchdog:1.0.0 -t k8s-watchdog:latest -f ./docker/Dockerfile .
      ```
   ##### Use image published on DockerHub
      1. Pull the image 
      ``` bash
      docker pull dserio83/k8s-watchdog
      ```
3. Create docker volumes:
   1. Create a volume for store logs
      ``` bash
      docker volume create k8s_watchdog_vol
      ```
   2. Create a volume for config data.
      ``` bash
      docker volume create k8s_watchdog_config
      ```
4. Copy the kube config file into the volume created. It contains the credentials for the k8s API.
Generally it is in /home/< user >/.kube/config folder.

   ``` bash
   docker container create --name copy-file -v k8s_watchdog_config:/config hello-world
   docker cp <path config file yaml> copy-file:/config/config.yaml
   docker rm copy-file
   ```
5. Create the stack and run it

    ``` bash
     docker-compose  -f ./docker/docker-compose.yaml -p k8s-watchdog-stack  up -d
    ```

### Run in Kubernetes

1. Configuration
   1. Navigate to the [k8s](k8s) folder
   2. Create and edit .env file under k8s folder, you can start from [.env.template](k8s/.env.template)
  
   3. Export .env

      ``` bash
      export $(cat .env | xargs)
      ```

      Checks that the variables have been exported:

      ``` bash
      printenv | grep K8SW_* 
      ```
 
2. Setup docker image:

   1. Navigate to the root folder
   2. Build image

        ``` bash
        docker build --target k8s-watchdog -t ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE}:1.0.0 -t ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE}:latest -f ./docker/Dockerfile .
        ```

   3. Push image

        ``` bash
        docker push ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE} --all-tags
        ```

      >[!INFO]  
      Alternative you can use skip the *Build image* and *Push image* steps and use an deployed image published on DockerHub.<br>
      Edit the .env file:
      **K8SW_DOCKER_REGISTRY=dserio83** <br>
      More info: https://hub.docker.com/r/dserio83/k8s-watchdog

3. Kubernetes create objects

   1. Navigate to the [k8s](k8s) folder

   2. Create namespace:

        ``` bash
        cat 10_create_ns.yaml | envsubst | kubectl apply -f -
        ```

   3. Create the PVC:

       ``` bash
       cat 20_pvc.yaml | envsubst | kubectl apply -f -
       ```

   4. Create the ConfigMap:

       ``` bash
       cat 30_cm.yaml | envsubst | kubectl apply -f -
       ```
  
   5. Create the RBAC:

       ``` bash
        cat 40_rbac.yaml | envsubst | kubectl apply -f -
       ```
  
   6. Create the Deployment:

       ``` bash
        cat 50_deployment.yaml | envsubst | kubectl apply -f -
       ```

## Test Environment

The project is developed, tested and put into production on several clusters with the following configuration

1. Kubernetes v1.28.2

## How to Contribute

1. Fork the project
2. Create your feature branch

    ``` bash
    git checkout -b feature/new-feature
    ```

3. Commit your changes

    ``` bash
   git commit -m 'Add new feature'
   ```

4. Push to the branch

    ``` bash
   git push origin feature/new-feature
   ```

5. Create a new pull request

## License

This project is licensed under the [MIT License](LICENSE).

---

Feel free to modify this template according to your project's specific requirements.

In case you need more functionality, create a PR. If you find a bug, open a ticket.
