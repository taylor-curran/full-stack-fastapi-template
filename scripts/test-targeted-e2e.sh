#!/usr/bin/env bash

set -euo pipefail

docker compose down -v --remove-orphans
docker compose up -d db mailcatcher backend
docker compose up -d playwright

npm run test:karate:targeted
npm run test:playwright:targeted
