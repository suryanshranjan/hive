"""Gate 116: Gate 105's measurer (gates/gate105/measure105.py), with one fix found while making the targets: the
button's colour, width and shape are read from the button itself, not from the box around it (a <p> around a <button> read as the page's
colour). Everything else is Gate 105's, unchanged."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gate105'))
import measure105 as M
for old, new in (('out.button_bg = bg(el);', 'out.button_bg = bg(b);'),
                 ('const s = getComputedStyle(el), r = el.getBoundingClientRect();',
                  'const s = getComputedStyle(b), r = b.getBoundingClientRect();')):
    assert old in M.JS
    M.JS = M.JS.replace(old, new)
measure, score, dist = M.measure, M.score, M.dist
