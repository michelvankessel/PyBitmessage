#!/usr/bin/env python3

import shutil
import sys
from pathlib import Path


from setuptools import Extension, setup
from setuptools.command.install import install

from typing import List, Tuple, Sequence, Any

# Load version without modifying sys.path or importing
softwareVersion = "0.0.0"
with open(Path(__file__).parent / "src" / "version.py") as f:
    exec(f.read())

EXTRAS_REQUIRE: Any = {
    "docs": ["sphinx"],
    "gir": ["pygobject"],

    "notify2": ["notify2"],
    "opencl": ["pyopencl", "numpy"],
    "prctl": ["python_prctl"],
    "qrcode": ["qrcode"],
    'sound;platform_system=="Windows"': ["winsound"],
    "tor": ["stem"],
    "xdg": ["pyxdg"],
    "xml": ["defusedxml"],
}


class InstallCmd(install):
    """Custom setuptools install command preparing icons"""

    def run(self):
        Path("desktop/icons/scalable").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            "desktop/can-icon.svg", "desktop/icons/scalable/pybitmessage.svg"
        )
        Path("desktop/icons/24x24").mkdir(parents=True, exist_ok=True)
        shutil.copyfile("desktop/icon24.png", "desktop/icons/24x24/pybitmessage.png")

        return install.run(self)


if __name__ == "__main__":
    here = Path(__file__).parent.resolve()
    with open(here / "README.md") as f:
        README = f.read()

    with open(here / "requirements.txt", "r") as f:
        requirements = list(f.readlines())

    bitmsghash = Extension(
        "pybitmessage.bitmsghash.bitmsghash",
        sources=["src/bitmsghash/bitmsghash.cpp"],
        libraries=["pthread", "crypto"],
    )

    installRequires: List[str] = ["cryptography", "pycryptodome", "defusedxml", "jsonrpclib-pelix"]
    packages: List[str] = [
        "pybitmessage",
        "pybitmessage.bitmessageqt",
        "pybitmessage.bitmessagecurses",
        "pybitmessage.messagetypes",
        "pybitmessage.network",
        "pybitmessage.plugins",
        "pybitmessage.storage",
    ]
    package_data: Any = {
        "": [
            "bitmessageqt/*.ui",
            "bitmsghash/*.cl",
            "sslkeys/*.pem",
            "translations/*.ts",
            "translations/*.qm",
            "default.ini",
            "sql/*.sql",
            "images/*.png",
            "images/*.ico",
            "images/*.icns",
            "bitmessagekivy/main.kv",
            "bitmessagekivy/screens_data.json",
            "bitmessagekivy/kv/*.kv",
            "images/kivy/payment/*.png",
            "images/kivy/*.gif",
            "images/kivy/text_images*.png",
        ]
    }

    packages.extend(
        ["pybitmessage.bitmessagekivy", "pybitmessage.bitmessagekivy.baseclass"]
    )

    if os.environ.get("INSTALL_TESTS", False):
        packages.extend(
            [
                "pybitmessage.mockbm",
                "pybitmessage.backend",
                "pybitmessage.bitmessagekivy.tests",
            ]
        )
        package_data[""].extend(["bitmessagekivy/tests/sampleData/*.dat"])

    installRequires.append("msgpack")

    data_files: List[Tuple[str, Sequence[str]]] = [
        ("share/applications/", ["desktop/pybitmessage.desktop"]),
        (
            "share/icons/hicolor/scalable/apps/",
            ["desktop/icons/scalable/pybitmessage.svg"],
        ),
        ("share/icons/hicolor/24x24/apps/", ["desktop/icons/24x24/pybitmessage.png"]),
    ]

    try:
        import distro

        if distro.name() in ("Debian", "Ubuntu"):
            data_files += [("etc/apparmor.d/", ["packages/apparmor/pybitmessage"])]
    except ImportError:
        pass

    cmdclass: Any = {"install": InstallCmd}
    command_options: Any = {"build_sphinx": {"source_dir": ("setup.py", "docs")}}

    dist = setup(
        name="pybitmessage",
        version=softwareVersion,
        description="Reference client for Bitmessage: a P2P communications protocol",
        long_description=README,
        license="MIT",
        url="https://bitmessage.org",
        install_requires=installRequires,
        extras_require=EXTRAS_REQUIRE,
        classifiers=[
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.13 :: Only",
            "Topic :: Internet",
            "Topic :: Security :: Cryptography",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        python_requires=">=3.13",
        package_dir={"pybitmessage": "src"},
        packages=packages,
        package_data=package_data,
        data_files=data_files,
        ext_modules=[bitmsghash],
        zip_safe=False,
        entry_points={
            "bitmessage.gui.menu": [
                "address.qrcode = pybitmessage.plugins.menu_qrcode [qrcode]"
            ],
            "bitmessage.notification.message": [
                "notify2 = pybitmessage.plugins.notification_notify2[gir, notify2]"
            ],
            "bitmessage.notification.sound": [
                "theme.canberra = pybitmessage.plugins.sound_canberra",
                "file.gstreamer = pybitmessage.plugins.sound_gstreamer[gir]",
                "file.fallback = pybitmessage.plugins.sound_playfile[sound]",
            ],
            "bitmessage.indicator": [
                "libmessaging =pybitmessage.plugins.indicator_libmessaging [gir]"
            ],
            "bitmessage.desktop": [
                "freedesktop = pybitmessage.plugins.desktop_xdg [xdg]"
            ],
            "bitmessage.proxyconfig": [
                "stem = pybitmessage.plugins.proxyconfig_stem [tor]"
            ],
            "console_scripts": ["pybitmessage = pybitmessage.bitmessagemain:main"]
            if sys.platform[:3] == "win"
            else [],
        },
        scripts=["src/pybitmessage"],
        cmdclass=cmdclass,
        command_options=command_options,
    )
