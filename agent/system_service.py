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
    
    def uninstall_service(self) -> bool:
        """Uninstall the system service"""
        try:
            self.logger.info("Uninstalling service")
            
            # Stop service first
            self.stop_service()
            
            if self.platform == "macos":
                return self._uninstall_macos_service()
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
    
    def start_service(self) -> bool:
        """Start the system service"""
        try:
            if self.platform == "macos":
                result = subprocess.run(
                    ['launchctl', 'start', f"com.proactive-agent.{self.service_name}"],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
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
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
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

