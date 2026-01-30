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

@cli.group()
def audio():
    """Audio generation and manipulation."""
    pass

@audio.command()
@click.argument("text")
@click.option("--voice", default="default", help="Voice ID or name")
def synth(text, voice):
    """Synthesize speech from text."""
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
    import requests

    # Determine if path is a file or directory
    is_file = os.path.isfile(path)
    is_dir = os.path.isdir(path)

    if not is_file and not is_dir:
        click.echo(f"Error: Path '{path}' not found.", err=True)
        return
    
    # In a real implementation, you'd likely need to zip directories
    # and handle the upload via the bridge API. For now, we focus on files.
    if is_dir:
        click.echo("Pushing directories is not yet supported. Please push files individually.", err=True)
        return

    # Assume it's a file for now
    try:
        # The shadow-bridge API seems to have /api/upload/training-sample and /api/upload/song-audio
        # For a generic push, we might need a dedicated endpoint or determine file type.
        # For now, let's assume a generic upload endpoint or use a common one.
        # A more robust solution would involve determining the file type and selecting endpoint.
        
        # For demonstration, let's try hitting a generic-looking upload endpoint if one exists,
        # or we'll need to investigate shadow-bridge's actual file handling.
        # Looking at routes/music.py and routes/api.py, there are upload endpoints.
        # Let's try /api/upload/song-audio as a placeholder for file uploads.
        
        # A more correct approach would be to have a dedicated /upload/file endpoint.
        # For now, we'll simulate the process.
        
        # Let's assume a POST request to /api/upload/file with the file content
        # This requires a specific endpoint to be implemented in ShadowBridge
        # For now, we'll print a message indicating the intention.
        
        click.echo(f"Simulating push for file: {path}...")
        # Example of how it might work IF an endpoint existed:
        # with open(path, 'rb') as f:
        #     files = {'file': (os.path.basename(path), f)}
        #     response = requests.post("http://localhost:6767/api/upload/file", files=files)
        #     if response.status_code == 200:
        #         click.echo(f"Successfully pushed {path}")
        #     else:
        #         click.echo(f"Failed to push {path}: {response.text}", err=True)
        
        click.echo("Push functionality is a placeholder. Actual implementation requires an API endpoint in ShadowBridge.")

    except FileNotFoundError:
        click.echo(f"Error: File not found at {path}", err=True)
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)


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
