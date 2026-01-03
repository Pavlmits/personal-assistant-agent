#!/usr/bin/env python3
"""
Cleanup Script for Student Study Assistant
Reset setup and optionally clear data
"""

import os
import sys
import sqlite3
from pathlib import Path

def cleanup_databases(keep_conversations=False):
    """Clean up databases"""

    print("🧹 Student Study Assistant - Cleanup")
    print("=" * 50)

    databases = ['user_memory.db', 'agent_cache.db']

    if keep_conversations:
        print("\n📝 Clearing setup data (keeping conversations)...")
        try:
            conn = sqlite3.connect('user_memory.db')
            cursor = conn.cursor()

            # Clear only setup-related data
            cursor.execute("DELETE FROM user_profile WHERE key = 'setup_complete'")
            cursor.execute("DELETE FROM courses")
            cursor.execute("DELETE FROM assignments")
            cursor.execute("DELETE FROM goals")

            conn.commit()
            conn.close()

            print("✅ Setup data cleared")
            print("✅ Courses cleared")
            print("✅ Assignments cleared")
            print("✅ Goals cleared")
            print("✅ Conversations preserved")

        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\n🗑️  Deleting all data (full reset)...")

        for db_file in databases:
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                    print(f"✅ Deleted {db_file}")
                except Exception as e:
                    print(f"❌ Error deleting {db_file}: {e}")
            else:
                print(f"ℹ️  {db_file} not found (already clean)")

    # Clear cache database WAL files
    cache_files = ['agent_cache.db-shm', 'agent_cache.db-wal',
                   'user_memory.db-shm', 'user_memory.db-wal']

    for cache_file in cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except:
                pass  # Ignore errors on cache files

    print("\n" + "=" * 50)
    print("✨ Cleanup complete!")
    print("\nNext steps:")
    print("  1. Run: python run_streamlit.py")
    print("  2. Complete the student setup wizard")
    print("=" * 50)

def show_help():
    """Show help message"""
    print("""
Student Study Assistant - Cleanup Tool

Usage:
  python cleanup.py              # Full reset (delete everything)
  python cleanup.py --keep       # Clear setup but keep conversations
  python cleanup.py --help       # Show this help

Options:
  --keep    Keep conversation history, only clear setup data
  --help    Show this help message

Examples:
  python cleanup.py              # Start completely fresh
  python cleanup.py --keep       # Redo setup, keep chat history
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            show_help()
            sys.exit(0)
        elif sys.argv[1] == '--keep':
            cleanup_databases(keep_conversations=True)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Run 'python cleanup.py --help' for usage")
            sys.exit(1)
    else:
        # Confirm full reset
        print("⚠️  This will DELETE all data (conversations, setup, courses, assignments)!")
        response = input("Are you sure? Type 'yes' to continue: ")

        if response.lower() == 'yes':
            cleanup_databases(keep_conversations=False)
        else:
            print("Cancelled.")
            sys.exit(0)
