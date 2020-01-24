#!/bin/bash

mkdir -p ~/.streamlit/

cat <<EOF > ~/.streamlit/config.toml
[server]
headless = true
enableCORS = false
port = $PORT
EOF
