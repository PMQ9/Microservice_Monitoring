# VS Code Quick Reference

## Build Tasks (Ctrl+Shift+B)
- Start Local Server (default)
- Build Docker Images
- Check Status
- View Logs
- Stop Server
- Clean Up

## Run and Debug Panel (Ctrl+Shift+D)
Select from dropdown and press F5 to run in new terminal:

**Quick Commands:**
- Make Start
- Make Port Forward All
- Make Test
- Make Demo
- Make Stop

**Python Debugging:**
- Start & Debug Backend
- Start & Debug Frontend
- Debug Both Services
- Attach to Backend Pod
- Attach to Frontend Pod

## Quick Start

**Option 1: Using Run and Debug**
1. Ctrl+Shift+D
2. Select "Make Start" from dropdown
3. Press F5
4. Select "Make Port Forward All"
5. Press F5
6. Open http://localhost:3000

**Option 2: Using Build Tasks**
1. Ctrl+Shift+B → Start Local Server
2. Ctrl+Shift+P → Tasks: Run Task → Port Forward All Services
3. Open http://localhost:3000

All commands in Run and Debug open in separate terminals.
