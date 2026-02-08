import click
import sys
import os
import subprocess
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ---- Configuration via environment variables ----
SHADOW_ROOT = os.environ.get("SHADOW_ROOT", "C:\\shadow")
SHADOW_BRIDGE_DIR = os.path.join(SHADOW_ROOT, "shadow-bridge")
BRIDGE_API = os.environ.get("SHADOW_BRIDGE_URL", "http://localhost:6767/api")

# File transfer safety limit
MAX_PUSH_SIZE_MB = 50

# ---- Logging setup ----
LOG_DIR = os.path.join(str(Path.home()), ".shadowai", "logs")
LOG_FILE = os.path.join(LOG_DIR, "shadow-cli.log")


def _setup_logging():
    """Configure rotating file logger for CLI operations."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("shadow-cli")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        ))
        logger.addHandler(handler)
    return logger


log = _setup_logging()


@click.group()
@click.version_option(version="0.1.0-alpha")
def cli():
    """ShadowAI Unified CLI - Control your AI ecosystem from the terminal."""
    pass

@cli.group()
def bridge():
    """Manage the ShadowBridge background service."""
    pass

@bridge.command()
def start():
    """Start the ShadowBridge GUI/Service."""
    log.info("CLI: bridge start")
    click.echo("Starting ShadowBridge...")
    gui_script = os.path.join(SHADOW_BRIDGE_DIR, "shadow_bridge_gui.py")
    if os.path.exists(gui_script):
        # Run in background
        subprocess.Popen([sys.executable, gui_script],
                         cwd=SHADOW_BRIDGE_DIR,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        click.echo("ShadowBridge launched in a new console.")
    else:
        click.echo(f"Error: Could not find ShadowBridge at {gui_script}", err=True)

@bridge.command()
def status():
    """Check if ShadowBridge is running."""
    log.info("CLI: bridge status")
    # Simple check for the process name or port
    import psutil
    running = False
    for proc in psutil.process_iter(['name']):
        if "ShadowBridge" in proc.info['name'] or "shadow_bridge_gui" in proc.info['name']:
            running = True
            break

    if running:
        click.echo("ShadowBridge is currently RUNNING.")
    else:
        click.echo("ShadowBridge is NOT running.")

@cli.group()
def image():
    """Image generation commands."""
    pass

@image.command()
@click.argument("prompt")
@click.option("--model", default="sd-xl-turbo", help="Model to use")
@click.option("--steps", default=4, type=int, help="Inference steps")
def generate(prompt, model, steps):
    """Generate an image using the local backend."""
    log.info(f"CLI: image generate model={model}")
    img_cli = os.path.join(SHADOW_BRIDGE_DIR, "shadow_image_cli.py")
    if not os.path.exists(img_cli):
        click.echo("Error: shadow_image_cli.py not found.", err=True)
        return

    cmd = [sys.executable, img_cli, "generate", prompt, "--model", model, "--steps", str(steps)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Process the JSON output from the script
    if "<<<JSON_START>>>" in result.stdout:
        json_str = result.stdout.split("<<<JSON_START>>>")[1].split("<<<JSON_END>>>")[0]
        data = json.loads(json_str)
        if data.get("success"):
            click.echo(f"Image generated successfully: {data.get('file_path', 'Path not returned')}")
        else:
            click.echo(f"Generation failed: {data.get('error', 'Unknown error')}", err=True)
    else:
        click.echo(result.stdout)

@cli.group()
def audio():
    """Audio generation and manipulation."""
    pass

@audio.command()
@click.argument("text")
@click.option("--voice", default="default", help="Voice ID or name")
def synth(text, voice):
    """Synthesize speech from text."""
    log.info(f"CLI: audio synth voice={voice}")
    click.echo(f"Synthesizing: '{text}' using voice '{voice}'...")
    # This calls the Suno API client as a fallback for synthesis
    suno_cli = os.path.join(SHADOW_BRIDGE_DIR, "scripts", "suno_api_client.py")
    if os.path.exists(suno_cli):
        subprocess.run([sys.executable, suno_cli, "generate", text, "--voice", voice])
    else:
        click.echo("Error: suno_api_client.py not found.", err=True)

@audio.command()
@click.argument("input_path")
@click.option("--model", required=True, help="Voice model ID to use for conversion")
@click.option("--output", help="Output path for converted audio")
def convert(input_path, model, output):
    """Convert audio using RVC voice cloning."""
    log.info(f"CLI: audio convert model={model}")
    rvc_script = os.path.join(SHADOW_BRIDGE_DIR, "scripts", "rvc_convert_audio.py")
    if not os.path.exists(rvc_script):
        click.echo(f"Error: Could not find RVC script at {rvc_script}", err=True)
        return

    cmd = [sys.executable, rvc_script, "--input", input_path, "--model", model]
    if output:
        cmd += ["--output", output]

    click.echo(f"Starting RVC conversion for {input_path}...")
    subprocess.run(cmd)

@cli.group()
def video():
    """Video generation commands."""
    pass

@video.command()
@click.argument("prompt")
@click.option("--duration", default=5, type=int, help="Video duration in seconds")
@click.option("--output", help="Output path for video")
def generate(prompt, duration, output):
    """Generate a video clip from a prompt."""
    log.info(f"CLI: video generate duration={duration}")
    video_script = os.path.join(SHADOW_ROOT, "backend", "scripts", "generate_video.py")
    if not os.path.exists(video_script):
        click.echo(f"Error: Could not find video generation script at {video_script}", err=True)
        return

    if not output:
        output = os.path.join(SHADOW_ROOT, "temp", "cli_output.mp4")

    cmd = [sys.executable, video_script, "--prompt", prompt, "--duration", str(duration), "--output", output]
    click.echo(f"Starting video generation for: '{prompt}'...")
    subprocess.run(cmd)

@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def gemini(args):
    """Pass commands to the Gemini CLI."""
    log.info("CLI: gemini passthrough")
    gemini_script = os.path.join(SHADOW_ROOT, "gemini.ps1")
    if os.path.exists(gemini_script):
        subprocess.run(["powershell.exe", "-File", gemini_script] + list(args))
    else:
        click.echo("Error: gemini.ps1 not found in root.", err=True)

@cli.command()
def ping():
    """Verify connection to ShadowBridge."""
    log.info("CLI: ping")
    import requests
    try:
        response = requests.get(f"{BRIDGE_API}/status", timeout=2)
        if response.status_code == 200:
            click.echo("Successfully connected to ShadowBridge.")
        else:
            click.echo(f"ShadowBridge responded with status {response.status_code}.")
    except Exception:
        click.echo("Error: Could not reach ShadowBridge. Is it running?")

@cli.command()
@click.argument("path")
@click.option("--device", "device_id", help="Target device ID")
def push(path, device_id):
    """Push a file to your connected mobile device."""
    log.info(f"CLI: push path={path}")
    import requests
    if not os.path.isfile(path):
        click.echo(f"Error: Path '{path}' not found or is not a file.", err=True)
        return

    # File size safety check
    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb > MAX_PUSH_SIZE_MB:
        click.echo(f"Error: File is {file_size_mb:.1f}MB, exceeds {MAX_PUSH_SIZE_MB}MB limit.", err=True)
        return

    if not device_id:
        try:
            resp = requests.get(f"{BRIDGE_API}/devices")
            devices = resp.json(); devices = devices if isinstance(devices, list) else devices.get("devices", [])
            if not devices:
                click.echo("Error: No devices found. Pair your phone first.", err=True)
                return
            device_id = devices[0].get("id")
        except Exception:
            click.echo("Error: Could not reach ShadowBridge to find devices.", err=True)
            return

    click.echo(f"Pushing {path} ({file_size_mb:.1f}MB) to device {device_id}...")
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f)}
        data = {"device_id": device_id}
        resp = requests.post(f"{BRIDGE_API}/mobile/push", files=files, data=data)
        if resp.status_code == 200:
            click.echo("Successfully queued file for mobile sync.")
            log.info(f"CLI: push success path={path} device={device_id}")
        else:
            click.echo(f"Failed to push file: {resp.text}", err=True)
            log.warning(f"CLI: push failed path={path} status={resp.status_code}")

@cli.command()
@click.argument("file_id")
@click.option("--output", help="Output filename")
def pull(file_id, output):
    """Pull a file from the mobile sync queue by its ID."""
    log.info(f"CLI: pull file_id={file_id}")
    import requests

    # Overwrite confirmation
    if output and os.path.exists(output):
        if not click.confirm(f"File '{output}' already exists. Overwrite?"):
            click.echo("Cancelled.")
            return

    click.echo(f"Pulling file {file_id}...")
    resp = requests.get(f"{BRIDGE_API}/mobile/pull/{file_id}", stream=True)
    if resp.status_code == 200:
        filename = output or resp.headers.get("Content-Disposition", "pulled_file").split("filename=")[-1].strip('"')
        with open(filename, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        click.echo(f"Successfully pulled file to {filename}")
        log.info(f"CLI: pull success file_id={file_id} -> {filename}")
    else:
        click.echo(f"Failed to pull file: {resp.status_code} {resp.text}", err=True)
        log.warning(f"CLI: pull failed file_id={file_id} status={resp.status_code}")


def _api_request(method, path, data=None):
    """Make an API request to ShadowBridge."""
    import requests
    url = f"{BRIDGE_API}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=data or {}, timeout=30)
        return resp.json(), resp.status_code
    except requests.ConnectionError:
        click.echo("Error: Cannot reach ShadowBridge. Is it running on port 6767?", err=True)
        return None, 0
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None, 0


@cli.group()
def agent():
    """Manage autonomous AI agents."""
    pass


@agent.command()
@click.option("--count", default=5, type=int, help="Number of agents to spawn")
@click.option("--focus", default="backend-polish",
              type=click.Choice(["backend-polish", "android-focus", "bridge-focus"]),
              help="Focus area for agents")
@click.option("--provider", default="claude", help="CLI provider (claude, gemini, codex)")
@click.option("--model", default="claude-sonnet-4-20250514", help="Model ID")
@click.option("--config", default=None, type=click.Path(exists=True),
              help="JSON file with per-agent configs")
def start(count, focus, provider, model, config):
    """Start autonomous agent loop.

    Example: shadow agent start --count 5 --focus backend-polish
    """
    log.info(f"CLI: agent start count={count} focus={focus} provider={provider}")
    configs = None
    if config:
        with open(config, "r") as f:
            configs = json.load(f)

    payload = {
        "count": count,
        "focus": focus,
        "provider": provider,
        "model": model,
    }
    if configs:
        payload["configs"] = configs

    click.echo(f"Starting {count} autonomous agents (focus: {focus}, provider: {provider})...")
    data, code = _api_request("POST", "/autonomous/start", payload)

    if data and code == 200:
        status = data.get("status", {})
        click.echo(f"Autonomous loop started.")
        click.echo(f"  Agents: {len(status.get('agents', {}))}")
        click.echo(f"  Dashboard: http://localhost:6767/agents")
    elif data:
        click.echo(f"Failed: {data.get('error', 'Unknown error')}", err=True)


@agent.command()
def stop():
    """Stop all autonomous agents."""
    log.info("CLI: agent stop")
    click.echo("Stopping autonomous agents...")
    data, code = _api_request("POST", "/autonomous/stop")
    if data and code == 200:
        click.echo("Autonomous loop stopped.")
    elif data:
        click.echo(f"Failed: {data.get('error', 'Unknown error')}", err=True)


@agent.command()
def status():
    """Show autonomous agent status."""
    log.info("CLI: agent status")
    data, code = _api_request("GET", "/autonomous/status")
    if not data:
        return

    running = data.get("running", False)
    paused = data.get("paused", False)

    state = "PAUSED" if paused else ("RUNNING" if running else "STOPPED")
    click.echo(f"Status: {state}")

    if data.get("uptime"):
        click.echo(f"Uptime: {data['uptime']}")
    click.echo(f"Cycles: {data.get('cycle_count', 0)}")
    click.echo()

    # Agents table
    agents = data.get("agents", {})
    if agents:
        click.echo(f"Agents ({len(agents)}):")
        click.echo(f"  {'Name':<25} {'Role':<15} {'Provider':<10} {'Status':<10} {'Tasks':<6}")
        click.echo(f"  {'-'*25} {'-'*15} {'-'*10} {'-'*10} {'-'*6}")
        for aid, info in agents.items():
            click.echo(
                f"  {info.get('name', '?'):<25} "
                f"{info.get('role', '?'):<15} "
                f"{info.get('provider', '?'):<10} "
                f"{info.get('status', '?'):<10} "
                f"{info.get('tasks_completed', 0):<6}"
            )
    else:
        click.echo("No agents active.")

    click.echo()
    click.echo(f"Task Queue: {data.get('tasks_pending', 0)} pending, "
               f"{data.get('tasks_in_progress', 0)} in progress, "
               f"{data.get('tasks_completed', 0)} completed, "
               f"{data.get('tasks_failed', 0)} failed")

    # Build history
    builds = data.get("build_history", [])
    if builds:
        click.echo(f"\nBuilds ({len(builds)}):")
        for b in builds[-5:]:
            status_icon = "OK" if b.get("success") else "FAIL"
            click.echo(f"  [{status_icon}] {b.get('build_type', '?')} - "
                       f"{b.get('duration_seconds', 0):.0f}s - "
                       f"{b.get('timestamp', '?')}")


@agent.command()
def scan():
    """Run a code scan to find actionable tasks."""
    log.info("CLI: agent scan")
    click.echo("Scanning codebase for improvements...")
    data, code = _api_request("POST", "/autonomous/scan")

    if data and code == 200:
        click.echo(f"Found {data.get('tasks_found', 0)} tasks:")
        categories = data.get("categories", {})
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            click.echo(f"  {cat:<20} {count}")

        repos = data.get("repos", {})
        click.echo()
        for repo, count in repos.items():
            click.echo(f"  {repo}: {count} tasks")
    elif data:
        click.echo(f"Scan failed: {data.get('error', 'Unknown')}", err=True)


@agent.command()
def pause():
    """Pause autonomous task assignment (agents stay alive)."""
    log.info("CLI: agent pause")
    data, code = _api_request("POST", "/autonomous/pause")
    if data and code == 200:
        click.echo("Autonomous loop paused. Agents are idle.")
    elif data:
        click.echo(f"Failed: {data.get('error', 'Unknown error')}", err=True)


@agent.command()
def resume():
    """Resume autonomous task assignment."""
    log.info("CLI: agent resume")
    data, code = _api_request("POST", "/autonomous/resume")
    if data and code == 200:
        click.echo("Autonomous loop resumed.")
    elif data:
        click.echo(f"Failed: {data.get('error', 'Unknown error')}", err=True)


def main():
    cli()

if __name__ == "__main__":
    main()
