FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=one

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    locales \
    lsb-release \
    tzdata \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://ros.packages.techfak.net/gpg.key -o /etc/apt/keyrings/ros-one-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/ros-one-keyring.gpg] https://ros.packages.techfak.net noble main" > /etc/apt/sources.list.d/ros-one.list \
    && curl -fsSL https://olliewalsh.github.io/openmower-ros-one/openmower-ros-one.asc -o /etc/apt/keyrings/openmower-ros-one.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/openmower-ros-one.asc] https://olliewalsh.github.io/openmower-ros-one noble main" > /etc/apt/sources.list.d/openmower-ros-one.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-one-ros-base \
    python3-rosdep \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init || true \
    && echo "yaml https://raw.githubusercontent.com/olliewalsh/openmower-ros-one/main/rosdep/ros-one-noble.yaml" > /etc/ros/rosdep/sources.list.d/50-openmower-ros-one.list \
    && rosdep update

COPY ros_entrypoint.sh /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
