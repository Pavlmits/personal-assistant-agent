"""
System Service Integration
Handles system startup, daemon management, and OS integration
"""

import os
import sys
import json
import signal
import subprocess
import time
import atexit
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import psutil

class SystemServiceManager:
    """
    Manages system service integration for the proactive AI agent
    Handles startup, daemon management, and OS-specific integration
    """
    
    def __init__(self, service_name: str = "proactive-ai-agent"):
        self.service_name = service_name
        self.platform = self._detect_platform()
        self.service_dir = Path.home() / ".proactive-agent"
        self.service_dir.mkdir(exist_ok=True)
        
        # Service files
        self.pid_file = self.service_dir / f"{service_name}.pid"
        self.log_file = self.service_dir / f"{service_name}.log"
        self.config_file = self.service_dir / "service_config.json"
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_service_logging()
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        if sys.platform == "darwin":
            return "macos"
        elif sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("linux"):
            return "linux"
        else:
            return "unknown"
    
    def _setup_service_logging(self):
        """Setup logging for service operations"""
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def install_service(self, auto_start: bool = True) -> bool:
        """Install the agent as a system service"""
        try:
            self.logger.info(f"Installing service for platform: {self.platform}")
            
            if self.platform == "macos":
                return self._install_macos_service(auto_start)
            elif self.platform == "linux":
                return self._install_linux_service(auto_start)
            elif self.platform == "windows":
                return self._install_windows_service(auto_start)
            else:
                self.logger.error(f"Unsupported platform: {self.platform}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing service: {e}")
            return False
    
    def _install_macos_service(self, auto_start: bool) -> bool:
        """Install macOS LaunchAgent service"""
        try:
            # Create LaunchAgents directory
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            # Service plist file
            plist_file = launch_agents_dir / f"com.proactive-agent.{self.service_name}.plist"
            
            # Get current Python executable and script path
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            # Create plist content
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.proactive-agent.{self.service_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>background-service</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <{'true' if auto_start else 'false'}/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{self.log_file}</string>
    <key>StandardErrorPath</key>
    <string>{self.log_file}</string>
    <key>WorkingDirectory</key>
    <string>{Path(__file__).parent.parent}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>"""
            
            # Write plist file
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # Load the service
            if auto_start:
                result = subprocess.run(
                    ['launchctl', 'load', str(plist_file)],
                    capture_output=True, text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to load service: {result.stderr}")
                    return False
            
            self.logger.info(f"macOS service installed: {plist_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing macOS service: {e}")
            return False
    
    def _install_linux_service(self, auto_start: bool) -> bool:
        """Install Linux systemd service"""
        try:
            # Create systemd user service directory
            systemd_dir = Path.home() / ".config" / "systemd" / "user"
            systemd_dir.mkdir(parents=True, exist_ok=True)
            
            # Service file
            service_file = systemd_dir / f"{self.service_name}.service"
            
            # Get current Python executable and script path
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            # Create service content
            service_content = f"""[Unit]
Description=Proactive AI Agent Background Service
After=network.target

[Service]
Type=simple
ExecStart={python_exe} {script_path} background-service --daemon
Restart=always
RestartSec=10
User={os.getenv('USER')}
WorkingDirectory={Path(__file__).parent.parent}
StandardOutput=append:{self.log_file}
StandardError=append:{self.log_file}

[Install]
WantedBy=default.target
"""
            
            # Write service file
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            
            if auto_start:
                subprocess.run(['systemctl', '--user', 'enable', f"{self.service_name}.service"], check=True)
                subprocess.run(['systemctl', '--user', 'start', f"{self.service_name}.service"], check=True)
            
            self.logger.info(f"Linux systemd service installed: {service_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing Linux service: {e}")
            return False
    
    def _install_windows_service(self, auto_start: bool) -> bool:
        """Install Windows service"""
        try:
            # For Windows, we'll create a startup entry instead of a full service
            # This is simpler and doesn't require admin privileges
            
            startup_dir = Path(os.getenv('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create batch file for startup
            batch_file = startup_dir / f"{self.service_name}.bat"
            
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            batch_content = f"""@echo off
cd /d "{Path(__file__).parent.parent}"
"{python_exe}" "{script_path}" background-service --daemon
"""
            
            if auto_start:
                with open(batch_file, 'w') as f:
                    f.write(batch_content)
                
                self.logger.info(f"Windows startup entry created: {batch_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing Windows service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the system service"""
        try:
            self.logger.info("Uninstalling service")
            
            # Stop service first
            self.stop_service()
            
            if self.platform == "macos":
                return self._uninstall_macos_service()
            elif self.platform == "linux":
                return self._uninstall_linux_service()
            elif self.platform == "windows":
                return self._uninstall_windows_service()
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error uninstalling service: {e}")
            return False
    
    def _uninstall_macos_service(self) -> bool:
        """Uninstall macOS LaunchAgent service"""
        try:
            plist_file = Path.home() / "Library" / "LaunchAgents" / f"com.proactive-agent.{self.service_name}.plist"
            
            if plist_file.exists():
                # Unload service
                subprocess.run(['launchctl', 'unload', str(plist_file)], capture_output=True)
                
                # Remove plist file
                plist_file.unlink()
                
                self.logger.info("macOS service uninstalled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling macOS service: {e}")
            return False
    
    def _uninstall_linux_service(self) -> bool:
        """Uninstall Linux systemd service"""
        try:
            service_file = Path.home() / ".config" / "systemd" / "user" / f"{self.service_name}.service"
            
            if service_file.exists():
                # Stop and disable service
                subprocess.run(['systemctl', '--user', 'stop', f"{self.service_name}.service"], capture_output=True)
                subprocess.run(['systemctl', '--user', 'disable', f"{self.service_name}.service"], capture_output=True)
                
                # Remove service file
                service_file.unlink()
                
                # Reload systemd
                subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)
                
                self.logger.info("Linux systemd service uninstalled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling Linux service: {e}")
            return False
    
    def _uninstall_windows_service(self) -> bool:
        """Uninstall Windows startup entry"""
        try:
            startup_dir = Path(os.getenv('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            batch_file = startup_dir / f"{self.service_name}.bat"
            
            if batch_file.exists():
                batch_file.unlink()
                self.logger.info("Windows startup entry removed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling Windows service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the system service"""
        try:
            if self.platform == "macos":
                result = subprocess.run(
                    ['launchctl', 'start', f"com.proactive-agent.{self.service_name}"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            elif self.platform == "linux":
                result = subprocess.run(
                    ['systemctl', '--user', 'start', f"{self.service_name}.service"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            elif self.platform == "windows":
                # For Windows, we'll start the process directly
                return self._start_windows_process()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the system service"""
        try:
            # First try to stop gracefully using PID file
            if self.pid_file.exists():
                try:
                    with open(self.pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        process.terminate()
                        process.wait(timeout=10)
                        self.logger.info(f"Stopped process with PID: {pid}")
                        
                        # Remove PID file
                        self.pid_file.unlink()
                        return True
                        
                except Exception as e:
                    self.logger.warning(f"Error stopping via PID file: {e}")
            
            # Platform-specific stop
            if self.platform == "macos":
                result = subprocess.run(
                    ['launchctl', 'stop', f"com.proactive-agent.{self.service_name}"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            elif self.platform == "linux":
                result = subprocess.run(
                    ['systemctl', '--user', 'stop', f"{self.service_name}.service"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            elif self.platform == "windows":
                # Kill any running processes
                return self._stop_windows_process()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
            return False
    
    def _start_windows_process(self) -> bool:
        """Start Windows background process"""
        try:
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"
            
            # Start process in background
            process = subprocess.Popen(
                [python_exe, str(script_path), "background-service", "--daemon"],
                cwd=Path(__file__).parent.parent,
                stdout=open(self.log_file, 'a'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            )
            
            # Write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Windows process: {e}")
            return False
    
    def _stop_windows_process(self) -> bool:
        """Stop Windows background process"""
        try:
            # Find and kill processes
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = process.info['cmdline']
                    if cmdline and 'background-service' in ' '.join(cmdline):
                        process.terminate()
                        process.wait(timeout=10)
                        self.logger.info(f"Stopped process: {process.info['pid']}")
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Windows process: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        status = {
            'platform': self.platform,
            'service_name': self.service_name,
            'installed': False,
            'running': False,
            'pid': None,
            'uptime': None
        }
        
        try:
            # Check if service is installed
            if self.platform == "macos":
                plist_file = Path.home() / "Library" / "LaunchAgents" / f"com.proactive-agent.{self.service_name}.plist"
                status['installed'] = plist_file.exists()
                
            elif self.platform == "linux":
                service_file = Path.home() / ".config" / "systemd" / "user" / f"{self.service_name}.service"
                status['installed'] = service_file.exists()
                
            elif self.platform == "windows":
                startup_dir = Path(os.getenv('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                batch_file = startup_dir / f"{self.service_name}.bat"
                status['installed'] = batch_file.exists()
            
            # Check if service is running
            if self.pid_file.exists():
                try:
                    with open(self.pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        status['running'] = True
                        status['pid'] = pid
                        status['uptime'] = time.time() - process.create_time()
                    else:
                        # PID file exists but process is dead
                        self.pid_file.unlink()
                        
                except Exception:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
        
        return status
    
    def create_daemon_process(self):
        """Create a daemon process for the background service"""
        try:
            # Write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # Register cleanup on exit
            atexit.register(self._cleanup_daemon)
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            self.logger.info(f"Daemon process created with PID: {os.getpid()}")
            
        except Exception as e:
            self.logger.error(f"Error creating daemon process: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self._cleanup_daemon()
        sys.exit(0)
    
    def _cleanup_daemon(self):
        """Cleanup daemon resources"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            self.logger.info("Daemon cleanup completed")
        except Exception as e:
            self.logger.error(f"Error in daemon cleanup: {e}")
    
    def get_logs(self, lines: int = 50) -> List[str]:
        """Get recent service logs"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
            return []
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
            return []

# CLI interface for service management
def main():
    """CLI interface for service management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Proactive AI Agent Service Manager')
    parser.add_argument('action', choices=['install', 'uninstall', 'start', 'stop', 'status', 'logs'],
                       help='Service action to perform')
    parser.add_argument('--no-auto-start', action='store_true',
                       help='Do not auto-start service on install')
    parser.add_argument('--service-name', default='proactive-ai-agent',
                       help='Service name (default: proactive-ai-agent)')
    parser.add_argument('--log-lines', type=int, default=50,
                       help='Number of log lines to show (default: 50)')
    
    args = parser.parse_args()
    
    service_manager = SystemServiceManager(args.service_name)
    
    if args.action == 'install':
        auto_start = not args.no_auto_start
        success = service_manager.install_service(auto_start)
        print(f"Service installation: {'SUCCESS' if success else 'FAILED'}")
        
    elif args.action == 'uninstall':
        success = service_manager.uninstall_service()
        print(f"Service uninstallation: {'SUCCESS' if success else 'FAILED'}")
        
    elif args.action == 'start':
        success = service_manager.start_service()
        print(f"Service start: {'SUCCESS' if success else 'FAILED'}")
        
    elif args.action == 'stop':
        success = service_manager.stop_service()
        print(f"Service stop: {'SUCCESS' if success else 'FAILED'}")
        
    elif args.action == 'status':
        status = service_manager.get_service_status()
        print("Service Status:")
        print("=" * 30)
        for key, value in status.items():
            print(f"{key}: {value}")
        
    elif args.action == 'logs':
        logs = service_manager.get_logs(args.log_lines)
        print(f"Recent Service Logs ({len(logs)} lines):")
        print("=" * 50)
        for line in logs:
            print(line.rstrip())

if __name__ == '__main__':
    main()

