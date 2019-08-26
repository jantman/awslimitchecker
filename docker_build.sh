#!/bin/bash -x

set -x
set -e

if [ -z "$1" ]; then
    >&2 echo "USAGE: docker_build.sh [build|dockerbuild|push|dockerbuildtest]"
    exit 1
fi

function gettag {
    # if it's a build of a tag, return that right away
    [ ! -z "$TRAVIS_TAG" ] && { echo $TRAVIS_TAG; return 0; }
    # otherwise, prefix with PR number if available
    prefix=''
    [ ! -z "$TRAVIS_PULL_REQUEST" ] && [[ "$TRAVIS_PULL_REQUEST" != "false" ]] && prefix="PR${TRAVIS_PULL_REQUEST}_"
    ref="test_${prefix}$(git rev-parse --short HEAD)_$(date +%s)"
    echo "${ref}"
}

function getversion {
    python -c 'from awslimitchecker.version import _VERSION; print(_VERSION)'
}

function getbuildurl {
  [ ! -z "$TRAVIS_BUILD_WEB_URL" ] && { echo $TRAVIS_BUILD_WEB_URL; return 0; }
  echo "local"
}

function dockertoxbuild {
    tag=$(gettag)
    version=$(getversion)
    buildurl=$(getbuildurl)
    echo "Building Docker image..."
    docker build \
      --build-arg git_version="$(git rev-parse --short HEAD)" \
      --no-cache \
      -t "jantman/awslimitchecker:${tag}" .
    echo "Built image and tagged as: jantman/awslimitchecker:${tag}"
}

function dockerbuildtest {
    tag=$(gettag)
    dockertoxbuild
    ./dockertest.sh "jantman/awslimitchecker:${tag}"
}

if [[ "$1" == "dockerbuild" ]]; then
    dockertoxbuild
elif [[ "$1" == "dockerbuildtest" ]]; then
    dockerbuildtest
else
    >&2 echo "USAGE: do_docker.sh [dockerbuild|dockerbuildtest]"
    exit 1
fi
