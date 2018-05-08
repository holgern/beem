#!/usr/bin/env bash
COMM_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
COMM_COUNT=$(git rev-list --count HEAD)
BUILD="beempy-${COMM_TAG}-${COMM_COUNT}_linux.tar.gz"


rm -rf dist build locale
pip install 
python setup.py clean
python setup.py build_ext
# python setup.py build_locales
pip install pyinstaller
pyinstaller beempy-onedir.spec

cd dist

tar -zcvf ${BUILD} beempy
if [ -n "$UPLOAD_LINUX" ]
then
    curl --upload-file ${BUILD} https://transfer.sh/
    # Required for a newline between the outputs
    echo -e "\n"
    md5sum  ${BUILD}
    echo -e "\n"
    sha256sum ${BUILD}
fi
