# AltServer-Linux — auto-recovery and easy setup

[日本語](README.md) | English

A fork of [NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux), combining fixes in AltServer itself with the recovery tools from [altserver-linux-native-autorecover](https://github.com/hinatamaxxx/altserver-linux-native-autorecover).

The direct parent is **NyaMisty's unofficial Linux port**, not an official Linux release from the AltStore team. Official AltServer source is available for [Windows](https://github.com/rileytestut/AltServer-Windows) and [macOS (inside AltStore)](https://github.com/altstoreio/AltStore/tree/classic/AltServer).

See [sources and URLs](docs/provenance.md) and the [official-source review and adoption policy](docs/upstream-review.md). Download and open the [HTML source directory](docs/sources.html) in a browser for links that open in a new tab. GitHub README links cannot force this behavior; use Ctrl+click (Command+click on Mac).

Setup installs AltServer, official netmuxd v0.4.3, Avahi, usbmuxd, Docker and local Anisette. AltServer and device discovery run on the host; Anisette runs in Docker. systemd starts and monitors the services.

## Quick start

The installer targets **Debian 12/13, amd64, with systemd**. Other architectures and Docker Desktop are outside its scope. Internet access is required. Debian 12 and clean physical-machine installation remain unverified.

```sh
git clone https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
sudo sh install.sh --prepare
```

**Preparation requires no iPhone or Apple account. AltServer remains inactive.** It installs dependencies and checksum-verified binaries, and pins Anisette to the digest of the image it pulled. Running without flags also performs preparation only.

Once prepared, connect one iPhone by USB, complete pairing/trust, and activate:

```sh
sudo sh install.sh --configure
sudo /usr/local/sbin/altserver-native-healthcheck
```

If the pairing record is missing, run `idevicepair pair` with the phone unlocked, respond to its Trust prompt, and rerun `sudo sh install.sh --configure`. Wi-Fi refresh requires a reachable phone and server on the same LAN and a valid pairing record. Tailscale provides remote administration; it does not replace Bonjour discovery or USB trust.

Alternatively, extract **AltServer-Linux-amd64-setup.tar.gz** from the release and run the same commands. It includes this fork's binary and setup files. Debian packages, netmuxd and Anisette are downloaded during preparation; this is not an offline installer.

**Setup stops without changing an existing installation.** See [setup and migration](docs/setup.md).

## Changes

- v0.2.0: Move the C++ base and device libraries to official repositories. Adopt authentication code from the official Windows 1.7.5 development source, with fixes for 2FA HTTP errors, authentication logging and unknown error codes. Address compatibility is handled at the input boundary. `VERSION` is the shared version source, exposed by `--version`. See the new [maintenance guide](docs/maintenance.md).
- v0.1.3: Remove the compatibility adapter and adopt jaakkopalvaila's libimobiledevice patch, so AltServer handles Linux/BSD IPv4 and IPv6 addresses directly. Address copy lengths are additionally bounded. This does not imply that the patch has been merged into official upstream.
- v0.1.2: Fix the Bonjour helper's 64-bit types and text/binary argument handling, and report registration API failures to the parent process. Following AltKeeper's approach, reject invalid JSON request lengths before reading the body and cap JSON frames at 4 MiB. This limit does not apply to IPA payloads.
- v0.1.1: Integrate Apple ID client-header and GSA connection fixes reported by other forks, plus the same ldid source as AltServer for Windows 1.7.4, to address signing errors on newer iOS versions. See the [fork review](docs/fork-review.md) for sources and selection decisions. Live Apple sign-in and operation on a physical iPhone remain unverified.
- Enable GSA TLS certificate validation, removing the inherited verification bypass.
- Parse Anisette timestamps as UTC regardless of the host timezone; validate dates and 64-bit routing info.
- Remove Anisette response values from debug output and set a 15-second HTTP request timeout.
- Fix `-h` / `--help`, missing install arguments, `-a` falling through to `-p`, unreadable IPA files and failure exit codes.
- Detect zero-byte transfers or invalid transfer sizes over USB instead of looping indefinitely.
- Preserve Anisette identity and provisioning state across container replacement.
- Connect AltServer directly to official netmuxd at `127.0.0.1:27015`; re-register the configured phone through its official API.
- Monitor and recover netmuxd directly. Check services even while the phone is away.

Recovery acts after three consecutive failures and uses a five-minute restart cooldown. Checks run 15 seconds after the preceding check finishes. `healthy` is a server/protocol result, not proof of a successful app refresh. `waiting_for_device` is expected while the phone is away. Automatic checks do not sign in to Apple or refresh apps.

## Validation and building

This fork is a **preview**. With v0.2.1 on an existing Debian server and an iPhone running iOS 27.0 / AltStore Classic 2.3, the user confirmed that an installed app opened after a refresh without another trust action. Clean installation, full-host reboot recovery and long-duration operation remain unverified. See [verification](docs/verification.md).

```sh
git clone --recursive https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
docker build -f docker/Dockerfile.build --target export --output type=local,dest=dist .
```

The upstream amd64 build environment compiles this fork's source and pinned submodules. Normal installation does not require that build environment. [Original upstream documentation](docs/upstream-readme.md) is retained for reference.

## Privacy, licenses and AI assistance

Never commit Apple credentials, pairing records, device identifiers, logs or Anisette state. Configuration is stored with mode 0600. Setup does not request Apple credentials.

AltServer-Linux retains [AGPL-3.0](LICENSE); imported recovery scripts retain [MIT](LICENSE.autorecover). Dependencies retain their respective licenses. See [provenance](docs/provenance.md).

This work used **GPT-6 Astra, High reasoning**, through Codex, verified from this session's metadata. **Gemini 3.8 Flash, High reasoning**, proofread the Japanese and English documentation. Earlier recovery work used GPT-6 Astra, Low reasoning, as recorded in the predecessor project. AI assistance is not evidence of device compatibility.
