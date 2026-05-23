# OpenMower ROS-O apt repository

This repository builds the missing OpenMower dependencies for Ubuntu 24.04 /
ROS-O, using Debian package names with the `ros-one-*` prefix. It builds from
bloom-generated Debian branches such as `debian/noetic/focal/<package>`, then
retargets the Debian metadata to ROS-O/Noble.

## Packages

Package inputs are defined in `packages.yaml`:

- `grid_map` subset: `grid_map_msgs`, `grid_map_core`, `grid_map_cv`, `grid_map_ros`, `grid_map_filters`
- `nmea_msgs`
- `rtcm_msgs`
- `ublox`

Only the grid_map packages used by OpenMower are built; optional packages such as `grid_map_octomap`, `grid_map_pcl`, demos, RViz plugins, and visualization are intentionally skipped.

`paho-mqtt-cpp` is not built here. It resolves to Ubuntu's native
`libpaho-mqttpp-dev` package on Noble.

## Build locally in Docker

Build binary `.deb` packages:

```bash
docker build -t openmower-ros-one .
docker run --rm -v "$PWD:/work" \
  -e DEBFULLNAME="Ollie Walsh" \
  -e DEBEMAIL="ollie.walsh@gmail.com" \
  -e INSTALL_BUILD_DEPS=1 \
  -e INSTALL_BUILT_DEBS=1 \
  openmower-ros-one \
  scripts/build_binary_packages.sh
sudo chown -R "$(id -u):$(id -g)" build out
```

Build one package or repository:

```bash
docker run --rm -v "$PWD:/work" \
  -e DEBFULLNAME="Ollie Walsh" \
  -e DEBEMAIL="ollie.walsh@gmail.com" \
  -e INSTALL_BUILD_DEPS=1 \
  -e INSTALL_BUILT_DEBS=1 \
  openmower-ros-one \
  scripts/build_binary_packages.sh --only nmea_msgs
sudo chown -R "$(id -u):$(id -g)" build out
```

Binary packages are written to `out/`. Rebuild versions default to the
`+rosone1` suffix so they sort after the bloom-generated distro version.

Create a local signed apt repository from `out/*.deb`:

```bash
APT_SIGN_KEYID=YOUR_KEY_FINGERPRINT scripts/create_apt_repo.sh
```

For throwaway local testing only, you can skip signing:

```bash
ALLOW_UNSIGNED=1 scripts/create_apt_repo.sh
```

## Code patches

Package-specific source patches live under `patches/<ros_package>/*.patch`.
They are applied after the release repository is checked out and before Debian
metadata is retargeted to ROS-O/Noble.

Example:

```text
patches/grid_map_core/0001-fix-noble-build.patch
patches/ublox_gps/0001-fix-boost-placeholders.patch
```

The build script applies them in filename sort order using `patch -p1`.

## GitHub Actions

The `Build apt repository` workflow builds binary `.deb` packages using the
ROS-O apt source on native GitHub-hosted runners for both `amd64` and `arm64`
(`ubuntu-24.04` and `ubuntu-24.04-arm`). It then merges both architectures into
one apt repository under `apt-repo/` and publishes it with GitHub Pages.

Repository settings needed:

- Enable GitHub Pages with source `GitHub Actions`.
- Add `APT_REPO_GPG_PRIVATE_KEY`; signed apt metadata is required for Pages publishing.
- Add `APT_REPO_GPG_KEYID`, preferably the full key fingerprint.
- Optional repository variables: `DEBFULLNAME` and `DEBEMAIL` for changelog identity.

Published users can add the repository with:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://olliewalsh.github.io/openmower-ros-one/openmower-ros-one.asc | \
  sudo tee /etc/apt/keyrings/openmower-ros-one.asc >/dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/openmower-ros-one.asc] https://olliewalsh.github.io/openmower-ros-one noble main" | \
  sudo tee /etc/apt/sources.list.d/openmower-ros-one.list
sudo apt update
```

## Use the rosdep overlay

For a local checkout:

```bash
sudo tee /etc/ros/rosdep/sources.list.d/50-openmower-ros-one.list >/dev/null <<EOF
yaml file://$PWD/rosdep/ros-one-noble.yaml
EOF
rosdep update
```

For the published repository:

```bash
sudo tee /etc/ros/rosdep/sources.list.d/50-openmower-ros-one.list >/dev/null <<EOF
yaml https://raw.githubusercontent.com/olliewalsh/openmower-ros-one/main/rosdep/ros-one-noble.yaml
EOF
rosdep update
```
