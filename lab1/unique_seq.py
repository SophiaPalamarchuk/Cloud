import re
import time
import sys

WORD_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄє']+")

def main():
    inp = sys.argv[1]
    out = sys.argv[2]

    t0 = time.time()
    words = set()

    with open(inp, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            for w in WORD_RE.findall(line.lower()):
                words.add(w)

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(words)) + "\n")

    print("unique_count =", len(words))
    print("time_sec =", round(time.time() - t0, 6))

if __name__ == "__main__":
    main()
