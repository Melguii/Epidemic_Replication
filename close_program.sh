#!/bin/bash
# shellcheck disable=SC2009
ps -fA | grep python | grep -v grep | awk '{print $2}' | xargs -r kill -2