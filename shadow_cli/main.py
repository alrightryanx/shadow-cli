import click
import sys
import os
import subprocess
import json

# Try to find the root shadow directory
# Assuming shadow-cli is at C:\shadow\shadow-cli
SHADOW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHADOW_BRIDGE_DIR = os.path.join(SHADOW_ROOT, "shadow-bridge")

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

@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def gemini(args):
    """Pass commands to the Gemini CLI."""
    gemini_script = os.path.join(SHADOW_ROOT, "gemini.ps1")
    if os.path.exists(gemini_script):
        subprocess.run(["powershell.exe", "-File", gemini_script] + list(args))
    else:
        click.echo("Error: gemini.ps1 not found in root.", err=True)

@cli.command()
def ping():
    """Verify connection to ShadowBridge."""
    import requests
    try:
        # Assuming ShadowBridge web dashboard is on 6767
        response = requests.get("http://localhost:6767/api/status", timeout=2)
        if response.status_code == 200:
            click.echo("Successfully connected to ShadowBridge.")
        else:
            click.echo(f"ShadowBridge responded with status {response.status_code}.")
    except Exception:
        click.echo("Error: Could not reach ShadowBridge. Is it running?")

@cli.command()
@click.argument("path")
def push(path):
    """Push a file or directory to your connected mobile device."""
    # Placeholder for future implementation
    click.echo(f"Feature coming soon: Pushing {path} to mobile...")

@cli.command()
@click.argument("path")
def pull(path):
    """Pull a file from your connected mobile device."""
    # Placeholder for future implementation
    click.echo(f"Feature coming soon: Pulling {path} from mobile...")

def main():
    cli()

if __name__ == "__main__":
    main()
