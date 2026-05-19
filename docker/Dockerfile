FROM ros:humble

SHELL ["/bin/bash", "-c"]

RUN apt update && apt install -y \
    git \
    vim \
    nano \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /rover_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
