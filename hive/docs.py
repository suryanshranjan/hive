"""The company's own documents (policies, handbooks, FAQs) given to a build with `hive start --docs <file or folder>`.

What the research found (Gates 7, 15-17, 20): documents settle the rules they cover completely, and twice overturned an
owner's own memory of a rule; but a document that waves at "the usual" or "the standard" misled builders into assuming
(Gate 16). So: the interview skips decisions the documents clearly settle, the builders follow them where they speak,
and where they are silent or vague the builders treat it as unknown and record an assumption for the owner."""
import os

TEXT = ('.md', '.markdown', '.txt', '.rst', '.csv')
LIMIT = 30000   # characters; a feature's policies, not a whole wiki

def read(path):
    """The documents' text, each under its file name, up to LIMIT characters. Empty if the path has none."""
    if not path or not os.path.exists(path):
        return ''
    files = [path] if os.path.isfile(path) else sorted(
        os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs if f.lower().endswith(TEXT))
    out, used = [], 0
    for f in files:
        try:
            text = open(f, encoding='utf-8', errors='replace').read().strip()
        except OSError:
            continue
        if not text:
            continue
        block = f"### {os.path.basename(f)}\n{text}\n"
        if used + len(block) > LIMIT:
            out.append(block[:max(0, LIMIT - used)] + '\n[... the rest was left out: too long]\n'); break
        out.append(block); used += len(block)
    return '\n'.join(out)

def instructions(text):
    """The documents as they go into the goal, for the interview planner and the builders."""
    if not text:
        return ''
    return ("\n\n## The company's own documents\nWhere these documents clearly settle a case, follow them and encode it "
            "as a test. Where they are silent, or only say \"as usual\" or \"the standard\" without saying what that is, "
            "treat it as unknown: do not assume what the usual is; decide, and record it as an assumption for the owner.\n\n"
            + text + '\n')
