"""Antigravity Autonomous Task Executor.

Runs in self-hosted GitHub Actions runner.
Solves tasks for each issue inside task-center/issue-<id>/.
Uses Google Gemini via Vertex AI / google-genai SDK.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def get_gcloud_token() -> str:
    """Retrieve OAuth2 access token via gcloud ADC."""
    try:
        res = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        # Fallback to gcloud core token
        res = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()


def init_workspace(issue_number: str) -> Path:
    """Initialize issue workspace directory and TASK.md using UTF-8."""
    base_dir = Path(__file__).resolve().parent.parent
    issue_dir = base_dir / f"issue-{issue_number}"
    issue_dir.mkdir(parents=True, exist_ok=True)
    task_file = issue_dir / "TASK.md"

    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")

    task_content = (
        f"# 任务目标: Issue #{issue_number}\n\n"
        f"**标题**: {title}\n\n"
        f"**需求详情**:\n{body}\n"
    )
    task_file.write_text(task_content, encoding="utf-8")
    print(f"[*] Workspace and TASK.md initialized with UTF-8: {task_file}")
    return issue_dir


def run_agent(issue_number: str):
    base_dir = Path(__file__).resolve().parent.parent
    issue_dir = base_dir / f"issue-{issue_number}"
    task_file = issue_dir / "TASK.md"
    report_file = issue_dir / "REPORT.md"

    if not task_file.exists():
        init_workspace(issue_number)

    task_content = task_file.read_text(encoding="utf-8")
    print(f"[*] Starting Antigravity Agent for Issue #{issue_number}...")
    print(f"[*] Workspace: {issue_dir}")

    # Tool definitions for local agent execution
    def tool_run_command(cmd: str) -> str:
        print(f"    [Tool: RunCommand] {cmd}")
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=str(issue_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            out = res.stdout + ("\nSTDERR:\n" + res.stderr if res.stderr else "")
            return out if out else "(Command completed with no output)"
        except Exception as e:
            return f"Error executing command: {e}"

    def tool_write_file(filename: str, content: str) -> str:
        target = (issue_dir / filename).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"    [Tool: WriteFile] Created {target.name} ({len(content)} bytes)")
        return f"Successfully wrote {filename}"

    def tool_read_file(filename: str) -> str:
        target = (issue_dir / filename).resolve()
        if not target.exists():
            return f"File {filename} does not exist."
        return target.read_text(encoding="utf-8")

    def tool_list_files() -> str:
        files = [f.name for f in issue_dir.iterdir() if f.is_file()]
        return json.dumps(files, ensure_ascii=False)

    # Initialize Gemini Client
    client = None
    try:
        from google import genai
        from google.genai import types

        # Check if VERTEX / GEMINI is configured
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "free-513908"
        os.environ["GOOGLE_CLOUD_LOCATION"] = "asia-east1"

        client = genai.Client()
        print("[*] Successfully connected to Vertex AI Gemini client.")
    except Exception as e:
        print(f"[*] Vertex AI client init notice: {e}, falling back to token/REST or direct mode.")

    system_instruction = (
        "You are the Antigravity Autonomous Engineering Agent running inside a GitHub Actions runner.\n"
        f"Your working directory is dedicated exclusively to Issue #{issue_number}: {issue_dir}.\n"
        "Your mission is to fully understand the user's requirement, write all required code/files, "
        "run tests or commands to verify correctness, and create a comprehensive REPORT.md summarizing what was accomplished.\n"
        "Always execute until the goal is fully achieved (/goal mode)."
    )

    if client:
        try:
            # We run agentic loop with tools
            tools = [tool_run_command, tool_write_file, tool_read_file, tool_list_files]
            prompt = (
                f"【任务指令】解决 Issue #{issue_number}\n\n"
                f"{task_content}\n\n"
                "请在当前工作区实现需求，编写必要代码，运行测试验证，并输出 REPORT.md。"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Fast and reliable
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=0.2,
                ),
            )
            final_text = response.text or ""
            print("[*] Gemini response received.")
            if not report_file.exists():
                report_file.write_text(
                    f"# Issue #{issue_number} 交付汇报\n\n{final_text}\n",
                    encoding="utf-8",
                )
        except Exception as exc:
            print(f"[!] Error in Gemini loop: {exc}")
            # Fallback simple report
            if not report_file.exists():
                report_file.write_text(
                    f"# Issue #{issue_number} 自动创建产物区\n\n已为该任务开辟独立空间并记录需求。\n\n需求详情:\n{task_content}\n",
                    encoding="utf-8",
                )
    else:
        # Fallback baseline record
        if not report_file.exists():
            report_file.write_text(
                f"# Issue #{issue_number} 产物工作区已建立\n\n已成功接收来自 AstrBot / GitHub 的需求派单。\n\n{task_content}\n",
                encoding="utf-8",
            )

    print(f"[*] Task #{issue_number} execution complete. REPORT.md generated.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_executor.py [init] <issue_number>")
        sys.exit(1)

    if sys.argv[1] == "init":
        if len(sys.argv) < 3:
            print("Usage: python agent_executor.py init <issue_number>")
            sys.exit(1)
        init_workspace(sys.argv[2])
    else:
        run_agent(sys.argv[1])
