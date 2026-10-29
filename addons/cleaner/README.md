# TV Cleaner

A fast, lightweight (~13 KB) on-device cleaner and memory booster designed specifically for Android TV and Amazon Fire TV.

## Features
- **1-Click Memory Boost:** Terminate background cached processes (`ActivityManager.killBackgroundProcesses()`) and free up RAM without restarting the TV.
- **Real-Time Memory & Storage Dashboard:** Live RAM (used/total/free/percentage) with MediaTek kernel underflow compensation, and real-time internal storage capacity.
- **Manage App Caches:** One-click shortcut into the TV's native application settings to clear heavy app caches (YouTube, Netflix, Hotstar).
- **TV & Remote Optimized:** Full D-pad navigation, high-contrast TV card layout, readable from couch distance.
- **Module Card Support:** Integrates with `com.gathin.tvhome` launcher as a home card.

## Build from Source
Build using JDK 17 and Android SDK 34:
```powershell
$env:JAVA_HOME="<path to JDK 17>"
$env:ANDROID_HOME="<path to Android SDK>"
.\launcher\gradlew.bat -p addons\cleaner assembleRelease
```
The output APK is at:
`addons/cleaner/app/build/outputs/apk/release/app-release.apk`

## Install to TV via ADB
```powershell
$env:TV_HOST="<tv ip>"
.\tools\venv\Scripts\python.exe tools/b64push.py addons/cleaner/app/build/outputs/apk/release/app-release.apk /data/local/tmp/cleaner.apk
.\tools\venv\Scripts\python.exe tools/tv.py "pm install -r /data/local/tmp/cleaner.apk; rm /data/local/tmp/cleaner.apk"
```
