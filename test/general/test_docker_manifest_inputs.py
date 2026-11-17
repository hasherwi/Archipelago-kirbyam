"""Exercise publication scripts without Docker or registry writes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


@unittest.skipUnless(sys.platform == "linux", "Publication jobs use Linux bash with readarray support")
class TestDockerManifestInputs(unittest.TestCase):
    def test_interleaved_builds_keep_each_manifest_in_one_run(self):
        workflow = yaml.safe_load((Path(__file__).parents[2] / ".github/workflows/docker.yml").read_text())
        build = next(s for s in workflow["jobs"]["build"]["steps"] if s.get("id") == "tags")
        merge = workflow["jobs"]["manifest"]["steps"][-1]
        self.assertEqual(build["env"]["BUILD_IMAGE"], merge["env"]["BUILD_IMAGE"])
        self.assertIn("github.run_id", build["env"]["BUILD_IMAGE"])
        self.assertNotIn("run_attempt", build["env"]["BUILD_IMAGE"])
        registry = {}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            docker = directory / "docker"
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$COMMAND_LOG"\n')
            docker.chmod(0o755)
            for run, architecture in [(1, "amd64"), (1, "arm64"), (2, "arm64")]:
                output = directory / "outputs"
                output.write_text("")
                env = dict(os.environ, BUILD_IMAGE=f"example/image:run-{run}", GITHUB_OUTPUT=str(output))
                script = build["run"].replace("${{ needs.prepare.outputs.tags }}", "example/image:nightly")
                script = script.replace("${{ matrix.suffix }}", architecture)
                subprocess.run(["bash", "-eu", "-c", script], env=env, check=True)
                tags = output.read_text().strip().removeprefix("tags=").split(",")
                for tag in tags:
                    registry[tag] = run
            log = directory / "commands"
            self.assertEqual([registry[f"example/image:nightly-{a}"] for a in ("amd64", "arm64")], [1, 2])
            env = dict(os.environ, BUILD_IMAGE="example/image:run-1", COMMAND_LOG=str(log),
                       PATH=f"{directory}:{os.environ['PATH']}")
            for target in ["example/image:nightly", "example/image:0.5.2\nexample/image:0.5"]:
                log.write_text("")
                script = merge["run"].replace("${{ needs.prepare.outputs.tags }}", target)
                subprocess.run(["bash", "-eu", "-c", script], env=env, check=True)
                creates = [line.split() for line in log.read_text().splitlines()
                           if line.startswith("manifest create ")]
                self.assertEqual(len(creates), len(target.splitlines()))
                for command in creates:
                    self.assertEqual([registry[tag] for tag in command[3:]], [1, 1])
