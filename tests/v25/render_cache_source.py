"""Build an explicit mixed comparison: current game + retained old cache function.

The rest of the current game stays byte-for-byte identical, so V25 scenery
fixes cannot be mistaken for cache raster differences. This is a diagnostic
reference, never a claimed complete V24 rendering or playable release.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cache_function(text):
    start = 'function cachedCyclistBody('
    end = '\nfunction drawCyclist('
    assert text.count(start) == 1 and text.count(end) == 1, 'Exact cache function boundary'
    first = text.index(start)
    return text[first:text.index(end, first)]


def build_sources(source, reference, folder):
    source, reference = source.resolve(), reference.resolve()
    current = source.read_text(encoding='utf-8')
    old = reference.read_text(encoding='utf-8')
    before, after = cache_function(old), cache_function(current)
    mixed = current.replace(after, before, 1)
    path = Path(folder) / 'mixed-cache-reference.html'
    path.write_text(mixed, encoding='utf-8')
    provenance = {
        'mode': 'Current source with ONLY cachedCyclistBody replaced by the retained reference function; all scenery, layout, simulation and body painter remain current. This is not a whole-V24 comparison.',
        'source': str(source), 'sourceSHA256': sha(source),
        'reference': str(reference), 'referenceSHA256': sha(reference),
        'referenceFunctionSHA256': hashlib.sha256(before.encode()).hexdigest(),
        'candidateFunctionSHA256': hashlib.sha256(after.encode()).hexdigest(),
        'mixedSHA256': sha(path),
    }
    return {'reference': path, 'candidate': source}, provenance
