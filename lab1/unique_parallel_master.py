import os
import subprocess
import time
import re

WORKER_IP = "10.0.0.6"
CORPUS = "corpus.txt"

WORD_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄє']+")

SSH_OPTS = [
    "-o", "ControlMaster=auto",
    "-o", "ControlPersist=60s",
    "-o", "ControlPath=/tmp/ssh_parcs_%r@%h:%p"
]

def extract_words(text: str):
    return set(WORD_RE.findall(text.lower()))

def adjust_split(path, mid, window=4096):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(mid)
        buf = f.read(min(window, size - mid))
        for i, b in enumerate(buf):
            if b in b" \n\t\r":
                return mid + i + 1
        f.seek(max(0, mid - window))
        buf = f.read(window)
  main()_ == "__main__":und(time.time() - t0, 6)))"utf-8") as f:ds_lab/{CORPUS} {mid} {size}"
