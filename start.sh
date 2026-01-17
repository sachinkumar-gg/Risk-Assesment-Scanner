#!/usr/bin/env bash
uvicorn api.index:app --host 0.0.0.0 --port 10000
