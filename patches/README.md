# Code patches

Put package-specific source patches here. The build script applies patches after
checking out the bloom release branch/tag and before retargeting Debian metadata.

Layout:

```text
patches/<ros_package>/*.patch
```

Example:

```text
patches/grid_map_core/0001-fix-noble-build.patch
patches/ublox_gps/0001-fix-boost-placeholders.patch
```

Patches are applied in filename sort order with:

```bash
patch -p1 -i <patch-file>
```

Create patches from inside a checked-out package directory with:

```bash
git diff > ../../patches/<ros_package>/0001-description.patch
```

Keep Debian packaging retargeting out of these patches unless the automatic
retargeting in `scripts/build_source_packages.py` is not sufficient.
