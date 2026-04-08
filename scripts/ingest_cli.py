#!/usr/bin/env python3
"""
CLI wrapper for the RAG ingestion endpoint.

Usage:
  python scripts/ingest_cli.py --topic school_anxiety
  python scripts/ingest_cli.py --topic school_anxiety --chunk-size 1000 --overlap 200 --force
"""

import argparse
import json
import sys

import requests

DEFAULT_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Trigger RAG document ingestion via the FastAPI endpoint.")
    parser.add_argument("--topic", required=True, help="Topic name (e.g. school_anxiety)")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion even if hash unchanged")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size in characters (default: 800)")
    parser.add_argument("--overlap", type=int, default=100, help="Chunk overlap in characters (default: 100)")
    parser.add_argument("--base-url", default=DEFAULT_BASE, help=f"Base URL of FastAPI server (default: {DEFAULT_BASE})")

    args = parser.parse_args()

    url = f"{args.base_url}/rag/ingest/{args.topic}"
    params = {
        "force": str(args.force).lower(),
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.overlap,
    }

    print(f"→ POST {url}")
    print(f"  params: chunk_size={args.chunk_size}, chunk_overlap={args.overlap}, force={args.force}")
    print()

    try:
        resp = requests.post(url, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except requests.exceptions.ConnectionError:
        print(" Could not connect to FastAPI server. Is it running?", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f" HTTP error: {e}", file=sys.stderr)
        try:
            print(json.dumps(resp.json(), indent=2), file=sys.stderr)
        except Exception:
            print(resp.text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
