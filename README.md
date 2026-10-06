# pia-wg
A WireGuard configuration utility for Private Internet Access.

This is a Python utility that generates WireGuard configuration files for the Private Internet Access VPN service. You can use the WireGuard protocol without PIA's proprietary client.

## Credit

This is a fork of [pia-wg](https://github.com/hsand/pia-wg) by **Harrison Sand** ([@hsand](https://github.com/hsand)).

Harrison built the original tool by reverse engineering PIA's [manual-connections](https://github.com/pia-foss/manual-connections) scripts, and turned that into a small program that logs in, registers a WireGuard key, and writes a config you can import. That work is the whole foundation of this project. The changes below only keep it working after PIA and Python moved on. Thank you, Harrison.

## What this fork changes

PIA's regional metadata servers now present an ExpressVPN certificate, so the bundled PIA CA can no longer verify the old token endpoint. Login uses PIA's current public token API instead:

`https://www.privateinternetaccess.com/api/client/v2/token`

Registering the WireGuard key still contacts the regional server by IP and checks the response against PIA's CA (`ca.rsa.4096.crt`). Python 3.13 and newer reject that CA unless strict X.509 verification is relaxed. This fork does that for the key-registration request. The certificate chain is still verified.

`.env` is listed in `.gitignore`, so a local env file is not committed. The script itself still asks for your username and password when you run it.

Python dependencies are declared in `pyproject.toml` and installed with [uv](https://docs.astral.sh/uv/). The direct dependencies are `requests`, `requests-toolbelt`, `urllib3`, and `pick`. `./setup.sh` checks for `uv`, the `wg` command, and those packages, and installs anything missing.

pia-wg runs on Windows, macOS, and Linux.

## Windows
* Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
* Install [WireGuard](https://www.wireguard.com/install/) so the `wg` command is on your PATH

Open a command prompt in this directory:

```
uv sync
uv run python generate-config.py
```

Follow the prompts. The script writes a `.conf` file that can be imported into the WireGuard app.

## macOS
Clone this fork and run the setup script. It installs `uv` and `wireguard-tools` with Homebrew when they are missing, then installs the Python packages:

```
git clone https://github.com/montest/pia-wg.git
cd pia-wg
./setup.sh
uv run python generate-config.py
```

Follow the prompts. `wireguard-tools` provides `wg` for key generation and `wg-quick` to start the tunnel:

```
sudo wg-quick up ./PIA-Iceland-1605054556.conf
sudo wg-quick down ./PIA-Iceland-1605054556.conf
```

## Linux (Debian/Ubuntu)
Clone this fork and run the setup script. It installs `uv` if needed, and `wireguard` plus `openresolv` when the `wg` command is missing, then installs the Python packages:

```
git clone https://github.com/montest/pia-wg.git
cd pia-wg
./setup.sh
uv run python generate-config.py
```

Copy the `.conf` file to `/etc/wireguard/`, and start the interface
```
sudo cp PIA-Iceland-1605054556.conf /etc/wireguard/wg0.conf
sudo wg-quick up wg0
```

You can shut down the interface with `sudo wg-quick down wg0`

## Check everything is working
Visit https://dnsleaktest.com/ to see your new IP and check for DNS leaks.
