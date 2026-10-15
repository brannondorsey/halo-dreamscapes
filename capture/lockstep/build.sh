#!/bin/sh -e
# Builds the lockstep shim for both ELF classes, so LD_PRELOAD='<dir>/out/$LIB/liblockstep.so' picks
# the right one (the 32-bit game under WINEARCH=win32, 64-bit helpers). Needs gcc-multilib, libgl-dev.
cd "$(dirname "$0")"
mkdir -p out/lib/x86_64-linux-gnu out/lib/i386-linux-gnu
CF="-O2 -Wall -Wno-nonnull-compare -fPIC -shared -fvisibility=hidden"
gcc      $CF -o out/lib/x86_64-linux-gnu/liblockstep.so lockstep.c -lpthread -ldl
gcc -m32 $CF -o out/lib/i386-linux-gnu/liblockstep.so lockstep.c -lpthread -ldl
