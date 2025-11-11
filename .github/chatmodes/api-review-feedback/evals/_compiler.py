#!/usr/bin/env python3
"""TypeSpec compiler integration for validation."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Tuple


class TypeSpecCompiler:
    """Handles TypeSpec compilation for validation."""

    @staticmethod
    def compile_client_tsp_in_context(client_tsp_content: str, spec_path: Path, build_dir: Path) -> Tuple[bool, str]:
        """
        Compile client.tsp in the context of the specification directory.
        Creates a temp copy of the spec directory under build/, injects client.tsp at the service root, and compiles with --no-emit.

        Args:
            client_tsp_content: Content of the client.tsp file to compile
            spec_path: Path to the specification directory (for import context)
            build_dir: Path to the build directory where temp spec will be created

        Returns:
            Tuple of (success, output)
        """
        try:
            # Find the repo root's node_modules
            current_file = Path(__file__).resolve()
            repo_root = current_file
            while repo_root.parent != repo_root:
                if (repo_root / "package.json").exists() and (repo_root / ".git").exists():
                    break
                repo_root = repo_root.parent

            repo_node_modules = repo_root / "node_modules"

            # Create temp directory under build/
            tmp_spec = build_dir / "temp_spec"

            # Clean up if it already exists
            if tmp_spec.exists():
                shutil.rmtree(tmp_spec)

            # Copy spec files
            shutil.copytree(spec_path, tmp_spec)

            # Find tspconfig.yaml to determine the service root directory
            tspconfig_candidates = list(tmp_spec.rglob("tspconfig.yaml"))
            if tspconfig_candidates:
                # Use the directory containing tspconfig.yaml as the service root
                service_root = tspconfig_candidates[0].parent
            else:
                # Fallback to tmp_spec root if no tspconfig.yaml found
                service_root = tmp_spec

            # Inject the client.tsp into the service root directory
            injected_client_path = service_root / "client.tsp"
            injected_client_path.write_text(client_tsp_content)

            # Run tsp compile on the client.tsp file with --no-emit from the service root
            result = subprocess.run(
                ["tsp", "compile", "./client.tsp", "--no-emit"],
                cwd=service_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env={**os.environ, "NODE_PATH": str(repo_node_modules)}
            )

            success = result.returncode == 0
            output = f"COMPILE STDOUT:\n{result.stdout}\n\nCOMPILE STDERR:\n{result.stderr}"

            return success, output

        except subprocess.TimeoutExpired:
            return False, "TypeSpec compilation timed out"
        except (OSError, subprocess.SubprocessError) as e:
            return False, f"Error running TypeSpec compilation: {str(e)}"
