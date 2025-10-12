#!/usr/bin/env python3
"""
Command-line interface for MergeMind secrets management.
"""

import argparse
import sys
import json
from typing import Optional
from secrets_manager import SecretsManager, SecretType

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="MergeMind Secrets Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Get secret command
    get_parser = subparsers.add_parser("get", help="Get a secret value")
    get_parser.add_argument("name", help="Secret name")
    get_parser.add_argument("--environment", "-e", default="production", help="Environment")
    get_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    # Set secret command
    set_parser = subparsers.add_parser("set", help="Set a secret value")
    set_parser.add_argument("name", help="Secret name")
    set_parser.add_argument("value", help="Secret value")
    set_parser.add_argument("--environment", "-e", default="production", help="Environment")
    set_parser.add_argument("--type", "-t", choices=[t.value for t in SecretType], default="secret-key", help="Secret type")
    
    # Rotate secret command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate a secret value")
    rotate_parser.add_argument("name", help="Secret name")
    rotate_parser.add_argument("--environment", "-e", default="production", help="Environment")
    
    # List secrets command
    list_parser = subparsers.add_parser("list", help="List available secrets")
    list_parser.add_argument("--environment", "-e", default="production", help="Environment")
    list_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    # Show metadata command
    metadata_parser = subparsers.add_parser("metadata", help="Show secret metadata")
    metadata_parser.add_argument("name", help="Secret name")
    metadata_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    # Check rotation command
    rotation_parser = subparsers.add_parser("check-rotation", help="Check rotation schedule")
    rotation_parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    # Export secrets command
    export_parser = subparsers.add_parser("export", help="Export secrets for environment")
    export_parser.add_argument("--environment", "-e", default="production", help="Environment")
    export_parser.add_argument("--format", "-f", choices=["text", "json"], default="json", help="Output format")
    
    # Import secrets command
    import_parser = subparsers.add_parser("import", help="Import secrets from file")
    import_parser.add_argument("file", help="Secrets file (JSON format)")
    import_parser.add_argument("--environment", "-e", default="production", help="Environment")
    
    # Generate secret command
    generate_parser = subparsers.add_parser("generate", help="Generate a new secret value")
    generate_parser.add_argument("--type", "-t", choices=[t.value for t in SecretType], default="secret-key", help="Secret type")
    generate_parser.add_argument("--length", "-l", type=int, default=32, help="Secret length")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        manager = SecretsManager()
        
        if args.command == "get":
            handle_get(manager, args)
        elif args.command == "set":
            handle_set(manager, args)
        elif args.command == "rotate":
            handle_rotate(manager, args)
        elif args.command == "list":
            handle_list(manager, args)
        elif args.command == "metadata":
            handle_metadata(manager, args)
        elif args.command == "check-rotation":
            handle_check_rotation(manager, args)
        elif args.command == "export":
            handle_export(manager, args)
        elif args.command == "import":
            handle_import(manager, args)
        elif args.command == "generate":
            handle_generate(manager, args)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_get(manager: SecretsManager, args):
    """Handle get command."""
    value = manager.get_secret(args.name, args.environment)
    
    if value is None:
        print(f"Secret '{args.name}' not found for environment '{args.environment}'", file=sys.stderr)
        sys.exit(1)
    
    if args.format == "json":
        output = {"name": args.name, "environment": args.environment, "value": value}
        print(json.dumps(output))
    else:
        print(value)

def handle_set(manager: SecretsManager, args):
    """Handle set command."""
    secret_type = SecretType(args.type)
    success = manager.set_secret(args.name, args.value, args.environment, secret_type)
    
    if success:
        print(f"Secret '{args.name}' set for environment '{args.environment}'")
    else:
        print(f"Failed to set secret '{args.name}'", file=sys.stderr)
        sys.exit(1)

def handle_rotate(manager: SecretsManager, args):
    """Handle rotate command."""
    success = manager.rotate_secret(args.name, args.environment)
    
    if success:
        print(f"Secret '{args.name}' rotated for environment '{args.environment}'")
    else:
        print(f"Failed to rotate secret '{args.name}'", file=sys.stderr)
        sys.exit(1)

def handle_list(manager: SecretsManager, args):
    """Handle list command."""
    secrets = manager.list_secrets(args.environment)
    
    if args.format == "json":
        output = {"environment": args.environment, "secrets": secrets}
        print(json.dumps(output))
    else:
        if secrets:
            print(f"Secrets for environment '{args.environment}':")
            for secret in secrets:
                print(f"  - {secret}")
        else:
            print(f"No secrets found for environment '{args.environment}'")

def handle_metadata(manager: SecretsManager, args):
    """Handle metadata command."""
    metadata = manager.get_secret_metadata(args.name)
    
    if metadata is None:
        print(f"Secret '{args.name}' not found", file=sys.stderr)
        sys.exit(1)
    
    if args.format == "json":
        print(json.dumps(metadata, indent=2))
    else:
        print(f"Metadata for secret '{args.name}':")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

def handle_check_rotation(manager: SecretsManager, args):
    """Handle check-rotation command."""
    secrets_to_rotate = manager.check_rotation_schedule()
    
    if args.format == "json":
        output = {"secrets_to_rotate": secrets_to_rotate}
        print(json.dumps(output))
    else:
        if secrets_to_rotate:
            print("Secrets that need rotation:")
            for secret in secrets_to_rotate:
                print(f"  - {secret}")
        else:
            print("No secrets need rotation")

def handle_export(manager: SecretsManager, args):
    """Handle export command."""
    secrets = manager.export_secrets(args.environment)
    
    if args.format == "json":
        print(json.dumps(secrets, indent=2))
    else:
        print(f"Exported secrets for environment '{args.environment}':")
        for name, value in secrets.items():
            print(f"  {name}={value}")

def handle_import(manager: SecretsManager, args):
    """Handle import command."""
    try:
        with open(args.file, 'r') as f:
            secrets_dict = json.load(f)
        
        manager.import_secrets(secrets_dict, args.environment)
        print(f"Imported {len(secrets_dict)} secrets for environment '{args.environment}'")
        
    except FileNotFoundError:
        print(f"File '{args.file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Invalid JSON in file '{args.file}'", file=sys.stderr)
        sys.exit(1)

def handle_generate(manager: SecretsManager, args):
    """Handle generate command."""
    secret_type = SecretType(args.type)
    value = manager._generate_secret_value(secret_type)
    print(value)

if __name__ == "__main__":
    main()
