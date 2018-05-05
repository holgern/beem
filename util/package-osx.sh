#!/usr/bin/env bash
if [ -z "$CI_BUILD_TAG" ]
then
    python setup.py patch_version --platform=osx
fi
VERSION=$(python -c 'import beem; print(beem.__version__)')

rm -rf dist build locale
pip install 
python setup.py clean
python setup.py build_ext
python setup.py build_locales
pip install pyinstaller
pyinstaller beempy-onedir.spec

cd dist
ditto -rsrc --arch x86_64 'beempy.app' 'beempy.tmp'
rm -r 'beempy.app'
mv 'beempy.tmp' 'beempy.app'
hdiutil create -volname "beempy $VERSION" -srcfolder 'beempy.app' -ov -format UDBZ "beempy $VERSION.dmg"
if [ -n "$UPLOAD_OSX" ]
then
    curl --upload-file "beempy $VERSION.dmg" https://transfer.sh/
    # Required for a newline between the outputs
    echo -e "\n"
    md5 -r "beempy $VERSION.dmg"
fi
