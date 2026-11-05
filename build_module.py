#!/usr/bin/env python3
"""
ViPERFX_RE Cross-Platform Build & Package Script
Builds libv4a_re.so for ARM64 / ARM32 using Android NDK and packages flashable Magisk module zip.
"""

import os
import sys
import shutil
import subprocess
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
OUT_DIR = os.path.join(SCRIPT_DIR, "out")
MOD_DIR = os.path.join(SCRIPT_DIR, "module")
MOD_OUT = os.path.join(OUT_DIR, "magisk_module")

# Find Android NDK and CMake
SDK_PATH = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
if not SDK_PATH:
    default_sdk = os.path.expanduser("~/AppData/Local/Android/Sdk")
    if os.path.exists(default_sdk):
        SDK_PATH = default_sdk

NDK_PATH = os.environ.get("ANDROID_NDK_HOME") or os.environ.get("ANDROID_NDK_ROOT")
if not NDK_PATH and SDK_PATH:
    ndk_parent = os.path.join(SDK_PATH, "ndk")
    if os.path.exists(ndk_parent):
        versions = sorted(os.listdir(ndk_parent))
        if versions:
            NDK_PATH = os.path.join(ndk_parent, versions[-1])

CMAKE_PATH = shutil.which("cmake")
NINJA_PATH = shutil.which("ninja")
if not CMAKE_PATH and SDK_PATH:
    cmake_parent = os.path.join(SDK_PATH, "cmake")
    if os.path.exists(cmake_parent):
        for v in sorted(os.listdir(cmake_parent), reverse=True):
            cand = os.path.join(cmake_parent, v, "bin", "cmake.exe" if os.name == "nt" else "cmake")
            if os.path.exists(cand):
                CMAKE_PATH = cand
                ninja_cand = os.path.join(cmake_parent, v, "bin", "ninja.exe" if os.name == "nt" else "ninja")
                if os.path.exists(ninja_cand):
                    NINJA_PATH = ninja_cand
                break

if not NDK_PATH or not CMAKE_PATH:
    print(f"Error: NDK ({NDK_PATH}) or CMake ({CMAKE_PATH}) not found!")
    sys.exit(1)

toolchain = os.path.join(NDK_PATH, "build", "cmake", "android.toolchain.cmake")
print(f"Using NDK: {NDK_PATH}")
print(f"Using CMake: {CMAKE_PATH}")

abis = ["arm64-v8a", "armeabi-v7a"]

for abi in abis:
    print(f"==> Building for ABI: {abi}...")
    abi_build = os.path.join(BUILD_DIR, abi)
    os.makedirs(abi_build, exist_ok=True)
    cmd = [
        CMAKE_PATH,
        "-B", abi_build,
        "-G", "Ninja" if NINJA_PATH else "Unix Makefiles",
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        f"-DANDROID_ABI={abi}",
        "-DANDROID_PLATFORM=android-21",
        "-DANDROID_ARM_NEON=TRUE",
        "-DCMAKE_BUILD_TYPE=Release",
        "-S", SCRIPT_DIR
    ]
    if NINJA_PATH:
        cmd.append(f"-DCMAKE_MAKE_PROGRAM={NINJA_PATH}")
    subprocess.check_call(cmd)
    subprocess.check_call([CMAKE_PATH, "--build", abi_build])

print("==> Packaging Magisk module...")
if os.path.exists(MOD_OUT):
    shutil.rmtree(MOD_OUT)
os.makedirs(os.path.join(MOD_OUT, "common", "files"), exist_ok=True)

# Copy base module files
for item in ['META-INF', 'module.prop', 'customize.sh', 'service.sh', 'uninstall.sh', 'LICENSE', 'system.prop', 'sepolicy.rule', 'aml.sh']:
    src = os.path.join(MOD_DIR, item)
    dst = os.path.join(MOD_OUT, item)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    elif os.path.isfile(src):
        shutil.copy2(src, dst)

# Copy common files
common_src = os.path.join(MOD_DIR, 'common')
for item in os.listdir(common_src):
    s = os.path.join(common_src, item)
    d = os.path.join(MOD_OUT, 'common', item)
    if os.path.isfile(s):
        shutil.copy2(s, d)

# Copy built libs
for abi in abis:
    so_src = os.path.join(BUILD_DIR, abi, "libv4a_re.so")
    if os.path.exists(so_src):
        shutil.copy2(so_src, os.path.join(MOD_OUT, "common", "files", f"libv4a_re_{abi}.so"))

# Touch skip mount markers
open(os.path.join(MOD_OUT, "skip_mount"), "w").close()
open(os.path.join(MOD_OUT, "skip_mountify"), "w").close()

# Package zip
zip_path = os.path.join(OUT_DIR, "ViPER4Android-RE-v2.1.1.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for r, dirs, files in os.walk(MOD_OUT):
        for f in files:
            full = os.path.join(r, f)
            rel = os.path.relpath(full, MOD_OUT)
            zf.write(full, rel)

print(f"Successfully created: {zip_path}")
