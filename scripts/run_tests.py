"""Explicit unit/full checks; a full run must never succeed by skipping data checks."""
import argparse
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--unit', action='store_true', help='Fast checks without the public dataset')
    mode.add_argument('--full', action='store_true', help='All checks after rebuilding the data')
    args = parser.parse_args()
    if args.full:
        required = [ROOT/'data/processed/retail.sqlite', ROOT/'data/processed/summary.json']
        if any(not p.is_file() for p in required):
            parser.error('Full checks require generated data. Run: python src/pipeline.py --download')
    sys.path.insert(0, str(ROOT/'tests'))
    import test_pipeline
    classes = [test_pipeline.CleaningTests, test_pipeline.AnalyticsTests]
    if args.full:
        classes.append(test_pipeline.RealOutputTests)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(c) for c in classes)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print('Unexpected skipped checks; this run is incomplete.', file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
