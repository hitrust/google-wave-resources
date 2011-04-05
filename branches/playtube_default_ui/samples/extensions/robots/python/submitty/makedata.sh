#!/bin/bash
#
# Used for generating the Python and JS files
# used by submitty.py and gadget.xml
# for determining allowed approvers.

JS=js/config.js
PY=config.py

approvers=('pamela.fox@googlewave.com' 'amandapsurya@googlewave.com' 'joe.gregorio@googlewave.com')
reviewlists=('google-wave-extensions-review@googlegroups.com')
reviewers=( ${approvers[@]} ${reviewlists[@]} )
gallerygroup='google-wave-extension-gallery-all@googlegroups.com'
gallerymod='doctorwave.gallery@googlewave.com'

ajs=$(printf ",'%s'" "${approvers[@]}")
ajs=${ajs:1}
ajs="var approvers = ["$ajs"]"
echo $ajs > $JS

apy=$(printf ",'%s'" "${approvers[@]}")
apy=${apy:1}
apy="APPROVERS = ["$apy"]"

rpy=$(printf ",'%s'" "${reviewers[@]}")
rpy=${rpy:1}
rpy="REVIEWERS = ["$rpy"]"
rgg="GALLERYGROUP = '$gallerygroup'"
rgm="GALLERYMOD = '$gallerymod'"
echo -e $apy"\n"$rpy"\n"$rgg"\n"$rgm > $PY
