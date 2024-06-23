# social_network

## Overview

Social Network application is a Django restframework application. This project is containerized using Docker for easy setup and deployment.

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)


## Installation Steps

1. **Clone the Repository**

   ```sh
   git clone https://github.com/Jagadisg/social_network.git

2. **Create virtual environment**
   
   ```sh
   python -m venv venv

3. **Build and Run the Docker Containers**

     **Build the Docker images and run the containers using Docker Compose.**

    ```sh
    docker-compose build
    docker-compose up

4. **Access the Application**

    **Once the containers are up and running, you can access the application in your web browser at:**

    ```sh
    http://localhost:8001

5. **Test api using swagger by accessing swagger endpoint which is easier than postman**

    ```sh
    http://localhost:8001/swagger/

#### If need you can use this credential to login using login endpoint.

    `email : "Roy@gmail.com"
     password: "Roy@12"`



