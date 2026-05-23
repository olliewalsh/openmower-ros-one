#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

import yaml


def run(cmd, cwd=None, env=None):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def sudo_cmd():
    sudo = os.environ.get('SUDO', '')
    return [sudo] if sudo else []


def deb_name(ros_name, prefix='ros-one'):
    return f"{prefix}-{ros_name.replace('_', '-')}"


def replace_in_file(path, replacements):
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r'ros-noetic-([A-Za-z0-9.+-]+)', lambda m: 'ros-one-' + m.group(1).lower(), text)
    if text != original:
        path.write_text(text)


def apply_code_patches(pkg_dir, package, patches_root):
    patch_dir = patches_root / package
    if not patch_dir.exists():
        return
    patches = sorted(p for p in patch_dir.iterdir() if p.suffix in {'.patch', '.diff'})
    for patch in patches:
        run(['patch', '-p1', '-i', str(patch.resolve())], cwd=pkg_dir)


def patch_debian_tree(pkg_dir, ros_pkg, codename, version_suffix):
    debian = pkg_dir / 'debian'
    if not debian.exists():
        raise RuntimeError(f'{pkg_dir} has no debian directory')

    replacements = [
        ('/opt/ros/noetic', '/opt/ros/one'),
        ('ROS_DISTRO=noetic', 'ROS_DISTRO=one'),
        ('ROS_DISTRO := noetic', 'ROS_DISTRO := one'),
        ('--rosdistro noetic', '--rosdistro one'),
        ('focal', codename),
    ]
    for path in debian.rglob('*'):
        if path.is_file():
            replace_in_file(path, replacements)

    source_name = deb_name(ros_pkg)
    changelog = debian / 'changelog'
    if changelog.exists():
        existing = changelog.read_text().splitlines()[0]
        match = re.search(r'\(([^)]+)\)', existing)
        base_version = match.group(1) if match else '0.0.0'
        if version_suffix not in base_version:
            new_version = f'{base_version}{version_suffix}'
        else:
            new_version = base_version
    else:
        new_version = f'0.0.0{version_suffix}'

    env = os.environ.copy()
    env.setdefault('DEBFULLNAME', 'OpenMower ROS-O Packaging')
    env.setdefault('DEBEMAIL', 'openmower@example.invalid')
    run(['dch', '--force-distribution', '--create' if not changelog.exists() else '--newversion', new_version,
         '--package', source_name, '--distribution', codename,
         'Rebuild for ROS-O on Ubuntu Noble.'], cwd=pkg_dir, env=env)

    control = debian / 'control'
    if control.exists():
        text = control.read_text()
        text = re.sub(r'^Source:\s*.*$', f'Source: {source_name}', text, flags=re.MULTILINE)
        package_name = source_name
        text = re.sub(r'^Package:\s*ros-one-[^\n]+$', f'Package: {package_name}', text, count=1, flags=re.MULTILINE)
        text = re.sub(r'^Package:\s*ros-noetic-[^\n]+$', f'Package: {package_name}', text, count=1, flags=re.MULTILINE)
        control.write_text(text)


def find_debian_package_dir(repo_dir):
    candidates = []
    for control in repo_dir.rglob('debian/control'):
        pkg_dir = control.parent.parent
        if (pkg_dir / 'debian/changelog').exists():
            candidates.append(pkg_dir)

    if not candidates:
        raise RuntimeError(f'{repo_dir} has no Debian package directory')

    if len(candidates) == 1:
        return candidates[0]

    root_candidate = repo_dir if (repo_dir / 'debian/control').exists() else None
    if root_candidate in candidates:
        return root_candidate

    joined = ', '.join(str(c) for c in candidates)
    raise RuntimeError(f'{repo_dir} has multiple Debian package directories: {joined}')


def checkout_package(repo_url, ref, work_dir, package):
    repo_dir = work_dir / f'{package}-release'
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    run(['git', 'clone', '--depth', '1', '--branch', ref, repo_url, str(repo_dir)])
    return repo_dir


def parse_changelog_field(pkg_dir, field):
    result = subprocess.run(
        ['dpkg-parsechangelog', f'--show-field={field}'],
        cwd=pkg_dir, text=True, stdout=subprocess.PIPE, check=True)
    return result.stdout.strip()


def source_name_and_upstream_version(pkg_dir):
    source = parse_changelog_field(pkg_dir, 'Source')
    version = parse_changelog_field(pkg_dir, 'Version')
    upstream = version.split('-', 1)[0]
    if ':' in upstream:
        upstream = upstream.split(':', 1)[1]
    return source, upstream


def ensure_orig_tarball(pkg_dir):
    source, upstream = source_name_and_upstream_version(pkg_dir)
    tarball = pkg_dir.parent / f'{source}_{upstream}.orig.tar.xz'
    if tarball.exists():
        return

    root_name = f'{source}-{upstream}'
    excluded_dirs = {'.git', 'debian', '.pc'}
    excluded_suffixes = {'.pyc'}
    print(f'+ create {tarball.name}', flush=True)
    with tarfile.open(tarball, 'w:xz') as tar:
        for path in sorted(pkg_dir.rglob('*')):
            rel = path.relative_to(pkg_dir)
            if any(part in excluded_dirs for part in rel.parts):
                continue
            if path.is_file() and path.suffix in excluded_suffixes:
                continue
            arcname = Path(root_name) / rel
            tar.add(path, arcname=str(arcname), recursive=False)


def move_artifacts(pkg_dir, out_dir, suffixes, include_tarballs=True):
    out_dir.mkdir(parents=True, exist_ok=True)
    moved = []
    parent = pkg_dir.parent
    for path in parent.iterdir():
        if path.suffix in suffixes or (include_tarballs and '.tar.' in path.name):
            target = out_dir / path.name
            if target.exists():
                target.unlink()
            shutil.move(str(path), target)
            moved.append(target)
    return moved


def build_source(pkg_dir, out_dir, sign):
    ensure_orig_tarball(pkg_dir)
    cmd = ['dpkg-buildpackage', '-S', '-sa', '-d']
    if not sign:
        cmd.extend(['-us', '-uc'])
    run(cmd, cwd=pkg_dir)
    move_artifacts(pkg_dir, out_dir, {'.changes', '.dsc', '.buildinfo'}, include_tarballs=True)


def install_build_deps(pkg_dir):
    if os.environ.get('INSTALL_BUILD_DEPS', '0') != '1':
        return
    run(sudo_cmd() + ['apt-get', 'build-dep', '-y', '--no-install-recommends', '.'], cwd=pkg_dir)


def install_built_debs(debs):
    if os.environ.get('INSTALL_BUILT_DEBS', '0') != '1':
        return
    debs = sorted(str(path) for path in debs if path.suffix == '.deb')
    if debs:
        cmd = sudo_cmd() + ['apt-get', 'install', '-y', '--no-install-recommends'] + debs
        try:
            run(cmd)
        except subprocess.CalledProcessError:
            print('+ apt-get install failed for built package; continuing because this may be a metapackage whose siblings are not built yet', flush=True)


def build_binary(pkg_dir, out_dir):
    install_build_deps(pkg_dir)
    cmd = ['dpkg-buildpackage', '-b', '-us', '-uc']
    run(cmd, cwd=pkg_dir)
    moved = move_artifacts(pkg_dir, out_dir, {'.deb', '.changes', '.buildinfo'}, include_tarballs=False)
    install_built_debs(moved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='packages.yaml')
    ap.add_argument('--out', default='out')
    ap.add_argument('--work', default='build')
    ap.add_argument('--only', action='append', help='ROS package name to build; may be repeated')
    ap.add_argument('--binary', action='store_true', help='Build binary .deb packages instead of source packages')
    ap.add_argument('--sign', action='store_true', help='Sign source changes for PPA upload')
    ap.add_argument('--patches', default='patches', help='Directory containing patches/<ros_package>/*.patch')
    ap.add_argument('--version-suffix', default='+rosone1')
    args = ap.parse_args()

    manifest = yaml.safe_load(Path(args.manifest).read_text())
    codename = manifest.get('ubuntu_codename', 'noble')
    selected = set(args.only or [])
    work = Path(args.work).resolve()
    out = Path(args.out).resolve()
    patches_root = Path(args.patches).resolve()
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    for repo_name, repo in manifest['repositories'].items():
        for package in repo['packages']:
            if selected and package not in selected and repo_name not in selected:
                continue
            ref_template = repo.get('debian_branch_template', repo['tag_template'])
            ref = ref_template.format(package=package, version=repo['version'])
            repo_dir = checkout_package(repo['release_repo'], ref, work, package)
            pkg_dir = find_debian_package_dir(repo_dir)
            apply_code_patches(pkg_dir, package, patches_root)
            patch_debian_tree(pkg_dir, package, codename, args.version_suffix)
            if args.binary:
                build_binary(pkg_dir, out)
            else:
                build_source(pkg_dir, out, args.sign)


if __name__ == '__main__':
    main()
