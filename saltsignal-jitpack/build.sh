#!/usr/bin/env bash
set -euo pipefail
set -x

ROOT="$PWD"
WORK="$ROOT/.jitpack-saltsignal"
rm -rf "$WORK"
mkdir -p "$WORK"

cat "$ROOT"/saltsignal-v5-build/part00.b64 \
    "$ROOT"/saltsignal-v5-build/part01.b64 \
    "$ROOT"/saltsignal-v5-build/part02.b64 \
    "$ROOT"/saltsignal-v5-build/part03.b64 \
    "$ROOT"/saltsignal-v5-build/part04.b64 \
    "$ROOT"/saltsignal-v5-build/part05.b64 \
    "$ROOT"/saltsignal-v5-build/part06.b64 > "$WORK/source.b64"
base64 -d "$WORK/source.b64" > "$WORK/source.zip"
echo 'd518308bfa024cb58a4d9b72daafa5f0ed345feb3ef39784fbee27d7e643a883  '"$WORK/source.zip" | sha256sum -c -
unzip -q "$WORK/source.zip" -d "$WORK/src"
PROJECT="$WORK/src/SaltSignalRecorder"

# Android SDK 35 is normally available on JitPack. Install it when sdkmanager is present.
if command -v sdkmanager >/dev/null 2>&1; then
  yes | sdkmanager --licenses >/dev/null 2>&1 || true
  sdkmanager 'platforms;android-35' 'build-tools;35.0.0' || true
elif [ -x "${ANDROID_HOME:-}/cmdline-tools/latest/bin/sdkmanager" ]; then
  yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses >/dev/null 2>&1 || true
  "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" 'platforms;android-35' 'build-tools;35.0.0' || true
fi

GRADLE_VERSION=8.9
GRADLE_DIR="$WORK/gradle-$GRADLE_VERSION"
if [ ! -x "$GRADLE_DIR/bin/gradle" ]; then
  curl -fL --retry 3 -o "$WORK/gradle.zip" "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
  unzip -q "$WORK/gradle.zip" -d "$WORK"
fi

"$GRADLE_DIR/bin/gradle" --no-daemon -p "$PROJECT" :app:assembleDebug
APK="$PROJECT/app/build/outputs/apk/debug/app-debug.apk"
test -s "$APK"
sha256sum "$APK"

GROUP_ID="${GROUP:-com.github.irstabyjorge}"
ARTIFACT_ID="${ARTIFACT:-AEGIS_SUPERSTACK}"
VERSION_ID="${VERSION:-jitpack-test}"
M2="$HOME/.m2/repository/${GROUP_ID//.//}/$ARTIFACT_ID/$VERSION_ID"
mkdir -p "$M2"
cp "$APK" "$M2/$ARTIFACT_ID-$VERSION_ID.apk"
cat > "$M2/$ARTIFACT_ID-$VERSION_ID.pom" <<POM
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>$GROUP_ID</groupId>
  <artifactId>$ARTIFACT_ID</artifactId>
  <version>$VERSION_ID</version>
  <packaging>apk</packaging>
</project>
POM
ls -l "$M2"
