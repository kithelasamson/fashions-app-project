[app]

title = MwananchiApp
package.name = mwananchiapp
package.domain = org.mwananchi

source.dir = .
source.include_exts = py,kv,png,jpg,json,ttf

version = 0.1

requirements = python3,kivy==2.3.1,pyjnius

orientation = portrait
fullscreen = 0

# Android permissions
android.permissions = INTERNET

# Target SDK (safe stable combo)
android.api = 33
android.minapi = 21

# NDK (important fix)
android.ndk = 25b
android.ndk_api = 21

# Architectures (keep modern first, optional 32-bit)
android.archs = arm64-v8a, armeabi-v7a

# AndroidX support
android.enable_androidx = True

# FIX: force APK (AAB causes your error)
android.release_artifact = apk
android.debug_artifact = apk

# Accept SDK license
android.accept_sdk_license = True

# Fix p4a compatibility
# p4a.branch = stable

[buildozer]
log_level = 2
warn_on_root = 1