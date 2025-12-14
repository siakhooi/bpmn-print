#!/bin/bash

# shellcheck disable=SC1091
source ./release.env

sed -i 'pyproject.toml' -e 's@^version = .*@version = "'"$RELEASE_VERSION"'"@'

echo "bpmn-print $RELEASE_VERSION" > tests/expected-output/cli-version.txt
