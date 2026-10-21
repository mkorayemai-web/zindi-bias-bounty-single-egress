"""Failure-propagation tests for the real serial runner scripts (fixture PY only)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from full_rebuild import prepare

ROOT = Path(__file__).resolve().parent.parent


class RebuildRunnerTests(unittest.TestCase):
    def test_drvplus_failure_propagates_and_no_done_marker(self):
        for script in ('run_stage.sh','run_stage_wa.sh','run_stage_all.sh'):
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                s=Path(tmp); (s/'egress').mkdir(); (s/'work').mkdir(); (s/'tables').mkdir()
                for name in ('run_stage.sh','run_stage_wa.sh','run_stage_all.sh'):
                    shutil.copy2(ROOT/'egress'/name,s/'egress'/name)
                fake=s/'fixture-python'
                fake.write_text('#!/bin/sh\nif [ "$1" = "build_edges.py" ] && [ "${3:-}" = "drvplus" ]; then exit 23; fi\nexit 0\n')
                fake.chmod(0o755)
                args=['sh',str(s/'egress'/script)] + (['northern-ca'] if script=='run_stage.sh' else [])
                proc=subprocess.run(args,env=dict(os.environ,PY=str(fake)),capture_output=True,text=True)
                self.assertNotEqual(proc.returncode,0)
                self.assertFalse((s/'work'/'stage_wa.done').exists())
                self.assertFalse((s/'work'/'stage_all.done').exists())

    def test_prepare_refuses_source_or_existing_scratch(self):
        with self.assertRaises(ValueError):
            prepare(ROOT,ROOT.parent,None)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                prepare(Path(tmp),ROOT.parent,None)


if __name__ == '__main__':
    unittest.main()
