#!/bin/bash
# ── ViZzo Deployment Script ──
# Ejecutar en el servidor VPS Linux (vizzovr.com) tras hacer cambios en el código.

git pull
docker compose build
docker compose up -d
