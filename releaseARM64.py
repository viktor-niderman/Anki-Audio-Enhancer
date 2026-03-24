#!/usr/bin/env python3

import sys, shutil, os, plistlib, subprocess
from sys import platform as _platform
from platform import processor as _processor
import argparse
import dmglib

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--nobuild", action="store_true", help="Dont rebuild before packaging")
parser.add_argument("-p", "--pkg", action="store_true", help="Only build .pkg")

def run(cmd):
  print(cmd)
  assert(not os.system(cmd))

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
RELEASE_DIR = os.path.join(PARENT_DIR, *["Releases", "ARM64"])

VERSION = "132.29.1.96"

def getVersion():
  return VERSION

def signWin(filename):
  INSTALLER_EXE = os.path.join(CURRENT_DIR, *["out", "primo", filename])
  SIGNTOOL_EXE = os.path.join(CURRENT_DIR, *["chrome", "tools", "build", "devel", "signtool.exe"])
  sign_command = '{} sign /tr http://timestamp.comodoca.com /td sha256 /fd sha256 /a \"{}\"'.format(SIGNTOOL_EXE, INSTALLER_EXE)
  print(sign_command)
  assert(not os.system(sign_command))

def extract_dmg(dmg_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if dmglib.dmg_already_attached(dmg_path):
        print(f"DMG already attached! {dmg_path}")
        dmglib.dmg_detach_already_attached(dmg_path)

    dmg_file = dmglib.DiskImage(dmg_path)
    mount_point = dmglib.DiskImage.attach(dmg_file)[0]

    try:
        print(f"DMG mounted at: {mount_point}")
        print("Contents of dmg:")
        for item in os.listdir(mount_point):
            print(item)

        app_src = os.path.join(mount_point, "PrimoBrowser.app")
        app_dst = os.path.join(output_dir, "PrimoBrowser.app")

        run(f'ditto "{app_src}" "{app_dst}"')
    finally:
        dmglib.dmg_detach_already_attached(dmg_path)

def makePKG(release_dir):
    ver = getVersion()
    pkgroot = os.path.join(release_dir, "pkgbuild")
    outroot = os.path.join(release_dir, "pkgs")
    plist_path = os.path.join(outroot, "component.plist")
    pkg_name = f"PrimoBrowser {ver} ARM64.pkg"
    pkg_path = os.path.join(outroot, pkg_name)
    dmg_name = f"PrimoBrowser-{VERSION}.dmg"
    dmg_file_path = os.path.join(release_dir, dmg_name)
    app_dst = os.path.join(pkgroot, "Applications", "PrimoBrowser.app")

    run(f"rm -rf '{pkgroot}' '{plist_path}'")
    run(f"mkdir -p '{pkgroot}/Applications' '{outroot}'")

    extract_dmg(dmg_file_path, os.path.join(pkgroot, "Applications"))

    run(f"xattr -cr '{app_dst}'")

    # Sign app
    run(
        f"codesign --force --deep --options runtime --timestamp "
        f'--sign "Developer ID Application: PrimoBrowser LLC (MQ9C8HCV2X)" '
        f"'{app_dst}'"
    )

    # Verify app signature
    run(f"codesign --verify --deep --strict --verbose=2 '{app_dst}'")

    # Generate component plist
    run(f"pkgbuild --analyze --root '{pkgroot}' '{plist_path}'")

    with open(plist_path, "rb") as f:
        plist = plistlib.load(f)

    for bundle in plist:
        if bundle.get("RootRelativeBundlePath") == "Applications/PrimoBrowser.app":
            bundle["BundleIsRelocatable"] = False
            bundle["BundleIsVersionChecked"] = True

    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f)

    # Build signed pkg
    run(
        f"pkgbuild "
        f"--root '{pkgroot}' "
        f"--component-plist '{plist_path}' "
        f"--install-location / "
        f"--identifier org.chromium.PrimoBrowser "
        f"--version '{ver}' "
        f'--sign "Developer ID Installer: PrimoBrowser LLC (MQ9C8HCV2X)" '
        f"'{pkg_path}'"
    )

    # Check pkg signature
    run(f"pkgutil --check-signature '{pkg_path}'")

def sign(platform):
  if platform == "win32":
    signWin("PrimoBrowser_installer.exe")
  elif platform == "darwin":
    sign_cmd = "./out/primo/PrimoBrowser\ Packaging/sign_chrome.py --input out/primo --output /tmp/releaseArm64 --identity 'MQ9C8HCV2X'  --installer-identity 'MQ9C8HCV2X'"
    sign_cmd += " --notary-arg=--apple-id=EMAIL --notary-arg=--team-id=MQ9C8HCV2X --notary-arg=--password=PASSWORD"
    run(sign_cmd)
    run(f"mv -fv /tmp/releaseArm64/*.dmg {RELEASE_DIR}")

def build(platform):
  if platform == "win32":
    assert(not os.system('ninja -C '+ os.path.join("out", "Release")+' primo mini_installer -j64'))
  elif platform == "darwin":
    assert(not os.system('autoninja -C '+ os.path.join("out", "primo")+' chrome chrome/installer/mac minidump_stackwalk -j 24'))

def main():
  args = parser.parse_args()
  if args.pkg:
    makePKG(RELEASE_DIR)
  elif args.nobuild:
    sign(_platform)
    makePKG(RELEASE_DIR)
  else:
    build(_platform)
    sign(_platform)
    makePKG(RELEASE_DIR)
if __name__== "__main__":
  main()
