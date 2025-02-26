#!/usr/bin/env bash
set -e

# Print nv2a debug messages to stdout
debug_nv2a=0

# Enable various OpenGL debugging functions.
debug_nv2a_gl=1

# Add a callback via glDebugMessageCallback to print OpenGL debug messages to
# stderr.
stream_gl_debug_messages=1

enable_renderdoc="--enable-renderdoc"

while [ ! -z "${1}" ]
do
  case "${1}" in
    '--nv2a'*)
      debug_nv2a=1
      shift
      ;;

    '--gl'*)
      debug_nv2a_gl=1
      stream_gl_debug_messages=1
      shift
      ;;

    '--renderdoc'*)
      enable_renderdoc="--enable-renderdoc"
      shift
      ;;

    '--no-nv2a'*)
      debug_nv2a=0
      debug_nv2a_gl=0
      stream_gl_debug_messages=0
      shift
      ;;

    '--no-gl'*)
      debug_nv2a_gl=0
      stream_gl_debug_messages=0
      shift
      ;;

    '--no-renderdoc'*)
      enable_renderdoc=" "
      shift
      ;;

    *)
      echo "Unknown argument ${1}"
      break
      ;;
  esac
done

set -u

cflags="-DDEBUG_NV2A=${debug_nv2a} \
      -DDEBUG_NV2A_GL=${debug_nv2a_gl} \
      -DSTREAM_GL_DEBUG_MESSAGES=${stream_gl_debug_messages}"

CFLAGS="${cflags}" \
      LDFLAGS="-L/home/abaire/bin/renderdoc/lib" \
      ./build.sh \
      --debug \
      -j8 \
      "${enable_renderdoc}"
