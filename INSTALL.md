# PyBitmessage Installation Instructions

- Binary (64bit, no separate installation of dependencies required)
  - Windows: <https://artifacts.bitmessage.at/winebuild/>
  - Linux AppImages: <https://artifacts.bitmessage.at/appimage/>
  - Linux snaps: <https://artifacts.bitmessage.at/snap/>
  - Mac (not up to date): <https://github.com/Bitmessage/PyBitmessage/releases/tag/v0.6.1>
- Source
    `git clone git://github.com/Bitmessage/PyBitmessage.git`

## Notes on the AppImages

The [AppImage](https://docs.appimage.org/introduction/index.html)
is a bundle, built by the
[appimage-builder](https://github.com/AppImageCrafters/appimage-builder) from
the Ubuntu Bionic deb files, the sources and `bitmsghash.so`, precompiled for
3 architectures, using the `packages/AppImage/AppImageBuilder.yml` recipe.

When you run the appimage the bundle is loop mounted to a location like
`/tmp/.mount_PyBitm97wj4K` with `squashfs-tools`.

The appimage name has several informational filds:

```bash
PyBitmessage-<VERSION>-g<COMMITHASH>[-alpha]-<ARCH>.AppImage
```

E.g. `PyBitmessage-0.6.3.2-ge571ba8a-x86_64.AppImage` is an appimage, built from
the `v0.6` for x86_64 and `PyBitmessage-0.6.3.2-g9de2aaf1-alpha-aarch64.AppImage`
is one, built from some development branch for arm64.

You can also build the appimage with local code. For that you need installed
docker:

```bash
docker build -t bm-appimage -f .buildbot/appimage/Dockerfile .
docker run -t --rm -v "$(pwd)"/dist:/out bm-appimage
```

The appimages should be in the dist dir.

## Helper Script for building from source

Go to the directory with PyBitmessage source code and run:

```bash
uv run checkdeps.py
```

If there are missing dependencies, it will explain what is missing. You need to repeat calling the script until no mandatory dependencies are missing.

### Manual Dependency Verification

PyBitmessage now requires **Python 3.13** and **PyQt6**.

#### For Debian-based (Ubuntu, others)

```bash
sudo apt install python3 python3-dev python3-venv openssl libssl-dev
uv pip install PyQt6 msgpack
```

#### For Arch Linux

```bash
sudo pacman -S python python-pyqt6 openssl
```

#### For macOS (via Homebrew)

```bash
brew install python@3.13 openssl@3
uv pip install PyQt6 msgpack
```

## Run with uv (Recommended for Modern Development)

This project is compatible with `uv` for fast dependency management.

```bash
# Run the application
uv run src/bitmessagemain.py

# Run tests
uv run tests.py
```

## Legacy / Manual Installation

### Install Dependencies

```bash
uv pip install PyQt6 msgpack
```

### Install PyBitmessage

```bash
uv pip install .
```

### Install from Requirements

```bash
uv pip install -r requirements.txt
```

## Development Environment

It is highly recommended to use `uv` for development.

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
uv run src/bitmessagemain.py
```

## Running Tests

To verify the installation, run the test suite:

```bash
uv run tests.py
```

## Alternative way to run PyBitmessage

Run `./start.sh` from the root directory.
