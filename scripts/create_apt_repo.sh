#!/usr/bin/env bash
set -euo pipefail

CODENAME="${CODENAME:-noble}"
COMPONENT="${COMPONENT:-main}"
ARCH="${ARCH:-$(dpkg --print-architecture)}"
ARCHES="${ARCHES:-}"
REPO_DIR="${REPO_DIR:-apt-repo}"
INPUT_DIR="${INPUT_DIR:-out}"
ORIGIN="${ORIGIN:-OpenMower ROS-O Dependencies}"
LABEL="${LABEL:-OpenMower ROS-O Dependencies}"
ALLOW_UNSIGNED="${ALLOW_UNSIGNED:-0}"

if ! compgen -G "${INPUT_DIR}/*.deb" >/dev/null; then
  echo "No .deb files found in ${INPUT_DIR}/" >&2
  exit 1
fi

rm -rf "${REPO_DIR}/dists/${CODENAME}" "${REPO_DIR}/pool/${COMPONENT}"
pool_dir="${REPO_DIR}/pool/${COMPONENT}"
mkdir -p "${pool_dir}"
cp "${INPUT_DIR}"/*.deb "${pool_dir}/"

if [[ -z "${ARCHES}" ]]; then
  mapfile -t detected_arches < <(dpkg-deb -f "${pool_dir}"/*.deb Architecture | sort -u)
  ARCHES="${detected_arches[*]}"
fi

for repo_arch in ${ARCHES}; do
  binary_dir="${REPO_DIR}/dists/${CODENAME}/${COMPONENT}/binary-${repo_arch}"
  mkdir -p "${binary_dir}"
  dpkg-scanpackages --arch "${repo_arch}" "${pool_dir}" /dev/null > "${binary_dir}/Packages"
  gzip -9cn "${binary_dir}/Packages" > "${binary_dir}/Packages.gz"
  xz -9ec "${binary_dir}/Packages" > "${binary_dir}/Packages.xz"
done

release="${REPO_DIR}/dists/${CODENAME}/Release"
cat > "${release}" <<EOF
Origin: ${ORIGIN}
Label: ${LABEL}
Suite: ${CODENAME}
Codename: ${CODENAME}
Architectures: ${ARCHES}
Components: ${COMPONENT}
Description: OpenMower ROS-O dependency packages
Date: $(date -Ru)
EOF

(
  cd "${REPO_DIR}/dists/${CODENAME}"
  echo 'MD5Sum:'
  for repo_arch in ${ARCHES}; do
    for f in ${COMPONENT}/binary-${repo_arch}/Packages ${COMPONENT}/binary-${repo_arch}/Packages.gz ${COMPONENT}/binary-${repo_arch}/Packages.xz; do
      printf ' %s %16d %s\n' "$(md5sum "$f" | awk '{print $1}')" "$(stat -c%s "$f")" "$f"
    done
  done
  echo 'SHA256:'
  for repo_arch in ${ARCHES}; do
    for f in ${COMPONENT}/binary-${repo_arch}/Packages ${COMPONENT}/binary-${repo_arch}/Packages.gz ${COMPONENT}/binary-${repo_arch}/Packages.xz; do
      printf ' %s %16d %s\n' "$(sha256sum "$f" | awk '{print $1}')" "$(stat -c%s "$f")" "$f"
    done
  done
) >> "${release}"

if [[ -n "${APT_SIGN_KEYID:-}" ]]; then
  gpg --batch --yes --local-user "${APT_SIGN_KEYID}" --clearsign -o "${release}.tmp" "${release}"
  mv "${release}.tmp" "${REPO_DIR}/dists/${CODENAME}/InRelease"
  gpg --batch --yes --local-user "${APT_SIGN_KEYID}" -abs -o "${REPO_DIR}/dists/${CODENAME}/Release.gpg" "${release}"
elif [[ "${ALLOW_UNSIGNED}" == "1" ]]; then
  echo "APT_SIGN_KEYID is unset; repository metadata was created unsigned." >&2
else
  echo "APT_SIGN_KEYID is required. Set ALLOW_UNSIGNED=1 only for local test repositories." >&2
  exit 2
fi
