"""Per-test results from JUnit XML (pytest --junitxml, jest-junit, vitest --reporter=junit, gotestsum, Maven...)."""
import xml.etree.ElementTree as ET

def results(path):
    """{test id: passed}. A test passes when its <testcase> has no <failure>, <error> or <skipped> child."""
    out = {}
    for tc in ET.parse(path).getroot().iter('testcase'):
        tid = '::'.join(x for x in (tc.get('classname') or tc.get('file') or '', tc.get('name') or '') if x)
        out[tid] = not any(child.tag in ('failure', 'error', 'skipped') for child in tc)
    return out
