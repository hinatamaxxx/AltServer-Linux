# Local anisette provider: Apple's Windows iCloud runtime under Wine.
# Apple's DLLs are not part of this image; install.sh --import-apple-runtime mounts them read-only.
FROM debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f AS helper
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++-mingw-w64-i686-win32 \
    && rm -rf /var/lib/apt/lists/*
COPY native-wine-anisette.cpp /src/
RUN i686-w64-mingw32-g++-win32 -std=c++17 -O2 -Wall -Wextra -static -static-libgcc -static-libstdc++ \
    -o /src/native-wine-anisette.exe /src/native-wine-anisette.cpp -lversion -lcrypt32

FROM debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
RUN dpkg --add-architecture i386 \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       wine wine32:i386 xvfb xauth python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV WINEARCH=win32 WINEPREFIX=/state/prefix WINEDEBUG=-all DISPLAY=:99 \
    WINEDLLOVERRIDES=mscoree,mshtml= TZ=UTC
COPY --from=helper /src/native-wine-anisette.exe /app/
COPY server.py start.sh /app/
RUN chmod 755 /app/start.sh && mkdir /state /apple
EXPOSE 6969
CMD ["/app/start.sh"]
