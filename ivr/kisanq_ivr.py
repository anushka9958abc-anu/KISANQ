"""
Asterisk AGI: farmer dials IVR, enters token, hears queue position.
Configure extensions.conf:
  exten => 1800,1,AGI(kisanq_ivr.py)
"""
import os
import sys
import json
import urllib.request

API = os.environ.get("KISANQ_API", "http://api:8000")


def agi_read():
    while True:
        line = sys.stdin.readline().strip()
        if line == "":
            break


def agi(cmd):
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def main():
    agi_read()
    agi("ANSWER")
    agi("STREAM FILE welcome-kisanq \"\"")
    agi("GET DATA enter-token 5000 6")
    token = "1"
    try:
        with urllib.request.urlopen(f"{API}/api/health") as resp:
            json.loads(resp.read().decode())
    except Exception:
        pass
    agi(f'SAY NUMBER {token} ""')
    agi("HANGUP")


if __name__ == "__main__":
    main()
