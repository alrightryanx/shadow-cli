# Shadow CLI (`shadow-cli`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg)]()

The unified command-line interface for the ShadowAI ecosystem. `shadow-cli` serves as the primary gateway for developers to interact with their AI assistants across multiple platforms (Android, PC, Web).

## 🌌 Overview

`shadow-cli` unifies the functionality previously spread across `gemini-cli`, `claude-shadow`, and various custom bridge scripts. It provides a robust, extensible framework for:

1.  **Backend Orchestration**: Seamlessly switch between Claude, Gemini, and local LLMs.
2.  **Cross-Device Communication**: Relay notifications and file transfers between your PC and the ShadowAI Android app.
3.  **Agent Coordination**: Manage multi-agent workflows using the AIDEV coordination layer.
4.  **Tool Execution**: Securely execute shell commands and file operations with remote mobile approval.

## 🚀 Quick Start

### Installation

```bash
# Install via pip
pip install shadow-cli

# Or install the development version from the root of the shadow repo
cd shadow-cli
pip install -e .
```

### Initial Setup

```bash
shadow init
```
This will guide you through connecting to your ShadowAI app and configuring your preferred AI backends.

## 🛠 Commands

### Core
- `shadow bridge`: Start/Status of the ShadowBridge service.
- `shadow ping`: Verify the connection to the background bridge.
- `shadow gemini`: Wrapper to pass commands directly to the Gemini CLI.

### Media & AI
- `shadow image generate`: Generate images using your local GPU backend.
- `shadow audio synth`: Synthesize speech from text.
- `shadow audio convert`: Clone voices using RVC.
- `shadow video generate`: Create video clips from text prompts.

### Mobile Sync (Alpha)
- `shadow push <file>`: Push files to your phone (placeholder implementation).
- `shadow pull <file>`: Pull files from your phone (placeholder implementation).

## 🔌 Integration

### Claude Code
Add the following to your Claude Code config:
```json
{
  "plugin": "shadow-cli",
  "enableNotifications": true
}
```

### Gemini CLI
`shadow-cli` acts as a drop-in replacement or wrapper for the standard Gemini CLI, providing enhanced ShadowAI features.

## 📂 Project Structure

- `shadow_cli/`: Core Python package.
- `plugins/`: Extensible plugin system for new backends and tools.
- `bridge/`: Logic for communicating with `shadow-bridge`.
- `aidev/`: Integration with the AIDEV coordination system.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
