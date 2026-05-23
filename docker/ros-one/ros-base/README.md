# ROS-O ros-base image

This image is the OpenMower ROS-O/Noble equivalent of `ros:noetic-ros-base-focal`.
It installs:

- Ubuntu 24.04 base
- ROS-O apt source from `https://ros.packages.techfak.net`
- OpenMower dependency apt repo from GitHub Pages
- `ros-one-ros-base`
- rosdep with the OpenMower rosdep overlay

Build locally:

```bash
docker build -t openmower-ros-one:ros-base docker/ros-one/ros-base
```

Run:

```bash
docker run --rm -it openmower-ros-one:ros-base
```
