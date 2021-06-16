#!/bin/bash +xe


ORIGINAL_PACKAGE_NAME='parseltongue'
ORIGINAL_MODULE_NAME='ptongue'


#---[ Check current Gemstone installation

if [[ -z "${GEMSTONE}" ]]; then
  GEMSTONE=/opt/gemstone/GemStone64Bit3.4.1-x86_64.Linux
  echo "No GEMSTONE environment variable set, using: $GEMSTONE"
fi

ENV_GEMSTONE_VER=$(echo $GEMSTONE | sed "s/.*GemStone64Bit\([0-9.]*\)-x86.*/\1/")

#---[ Determine required Gemstone installation

GEMSTONE_VER_FOR_PACKAGE=$1
if [[ -z "$GEMSTONE_VER_FOR_PACKAGE" ]]; then
  #use the version of the Gemstone installation
  GEMSTONE_VER_FOR_PACKAGE=$ENV_GEMSTONE_VER
fi
GEMSTONE_VER_FOR_PACKAGE=`echo $GEMSTONE_VER_FOR_PACKAGE | tr '.' '_'`
REQUIRED_GEMSTONE_VER=`echo $GEMSTONE_VER_FOR_PACKAGE | tr '_' '.' `

REQUIRED_GEMSTONE_INSTALLATION=$(echo $GEMSTONE | sed "s/${ENV_GEMSTONE_VER}/${REQUIRED_GEMSTONE_VER}/")
if [ ! -d "$REQUIRED_GEMSTONE_INSTALLATION" ]; then
  echo "Required Gemstone installation not found: $REQUIRED_GEMSTONE_INSTALLATION"
  exit 1
fi

#---[ Copy source code to new package that contains version info


DEST_ROOT_DIR=/tmp/parseltongue_for_$GEMSTONE_VER_FOR_PACKAGE
NEW_MODULE_NAME="${ORIGINAL_MODULE_NAME}_${GEMSTONE_VER_FOR_PACKAGE}"
DEST_DIR=$DEST_ROOT_DIR/$NEW_MODULE_NAME

function prepare_destination_dir() {
  if [ -d "${DEST_ROOT_DIR}" ]; then
    echo "Removing ${DEST_ROOT_DIR}..."
    rm -rf $DEST_ROOT_DIR
  fi
  echo "Creating dir ${DEST_ROOT_DIR}..."
  mkdir -p $DEST_DIR
}

prepare_destination_dir

ROOT_SOURCE_FILES=("setup.py" "setup.cfg")
for i in "${ROOT_SOURCE_FILES[@]}"; do
  cp $i $DEST_ROOT_DIR
  sed -i "s|${ORIGINAL_MODULE_NAME}|${NEW_MODULE_NAME}|g" $DEST_ROOT_DIR/$i
  #This attempts to fix the package name defined in setup.py
  sed -i "s|name='${ORIGINAL_PACKAGE_NAME}'|name='${ORIGINAL_PACKAGE_NAME}_${GEMSTONE_VER_FOR_PACKAGE}'|g" $DEST_ROOT_DIR/$i
done

MODULE_SOURCE_FILES=("__init__.py" "gemproxy.pxd" "gemproxy.pyx" "gemproxylinked.pyx" "gemproxyrpc.pyx" "gemstonecontrol.py")
for i in "${MODULE_SOURCE_FILES[@]}"; do
  cp $ORIGINAL_MODULE_NAME/$i $DEST_DIR
done

#---[ Compile new source package against required Gemstone version

function set_new_gemstone_installation_dir(){
  GEMSTONE=$REQUIRED_GEMSTONE_INSTALLATION
}

set_new_gemstone_installation_dir
(
cd $DEST_ROOT_DIR
python setup.py develop -N
python setup.py build_ext --inplace
python setup.py bdist_wheel
)
echo cp $DEST_ROOT_DIR/dist/* dist/
