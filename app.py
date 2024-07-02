import os
import re
import sys
import argparse
import yaml
import shutil
import logging
from datetime import datetime
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

class SubstitutionScript:
    def __init__(self, config_path, log_path, backup_dir, dry_run, verbose, force_scan, interactive, file_types):
        self.config_path = config_path
        self.log_path = log_path
        self.backup_dir = backup_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.force_scan = force_scan
        self.interactive = interactive
        self.file_types = file_types
        self.substitutions = self.load_config()
        self.processed_files = set()
        self.load_processed_files()
        self.setup_logging()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                if 'substitutions' not in config:
                    raise ValueError("Configuration file is missing 'substitutions' key.")
                return config['substitutions']
        except Exception as e:
            print(Fore.RED + f"Error loading configuration file: {e}")
            sys.exit(1)

    def load_processed_files(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r') as file:
                for line in file:
                    if "Processed file:" in line:
                        self.processed_files.add(line.split(":")[1].strip())

    def setup_logging(self):
        logging.basicConfig(filename=self.log_path, level=logging.INFO, format='%(asctime)s - %(message)s')

    def backup_file(self, file_path):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        shutil.copy(file_path, self.backup_dir)

    def process_file(self, file_path):
        if file_path in self.processed_files and not self.force_scan:
            if self.verbose:
                print(Fore.YELLOW + f"Skipping already processed file: {file_path}")
            return

        if self.verbose:
            print(Fore.GREEN + f"Processing file: {file_path}")

        self.backup_file(file_path)

        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return

        original_content = content
        for substitution in self.substitutions:
            pattern = substitution['pattern']
            replacement = substitution['replacement']
            if self.interactive:
                matches = re.findall(pattern, content)
                for match in matches:
                    confirm = input(f"Replace '{match}' with '{replacement}'? (y/n): ")
                    if confirm.lower() == 'y':
                        content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)

        if not self.dry_run:
            try:
                with open(file_path, 'w') as file:
                    file.write(content)
            except Exception as e:
                logging.error(f"Error writing to file {file_path}: {e}")
                return

        substitutions_count = len(re.findall('|'.join([sub['pattern'] for sub in self.substitutions]), original_content))
        logging.info(f"Processed file: {file_path} - Substitutions: {substitutions_count}")
        self.processed_files.add(file_path)

    def process_files(self, files):
        with ThreadPoolExecutor() as executor:
            executor.map(self.process_file, files)

    def generate_summary(self):
        print(Fore.CYAN + "Summary Report")
        print(Fore.CYAN + "==============")
        for file_path in self.processed_files:
            print(Fore.CYAN + f"Processed file: {file_path}")

    def run(self, target):
        try:
            if os.path.isfile(target):
                self.process_files([target])
            elif os.path.isdir(target):
                files = [os.path.join(target, f) for f in os.listdir(target) if f.endswith(tuple(self.file_types))]
                self.process_files(files)
            else:
                print(Fore.RED + "Invalid target specified.")
                sys.exit(1)
            self.generate_summary()
        except KeyboardInterrupt:
            print(Fore.RED + "\nProcess interrupted by user.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Substitution Script",
        epilog="""
        Example usage:
        python3 app.py filename.txt
        python3 app.py /path/to/directory
        python3 app.py filename.txt -f
        python3 app.py filename.txt -d
        python3 app.py filename.txt -v
        python3 app.py filename.txt -i
        python3 app.py filename.txt -l custom_log.log
        python3 app.py --tail 20
        python3 app.py filename.txt -c config.yaml
        python3 app.py filename.txt -c config.yml
        """
    )
    parser.add_argument('target', nargs='?', help="Target file or directory")
    parser.add_argument('-c', '--config', default='config.yaml', help="Path to configuration file")
    parser.add_argument('-l', '--log', default='substitution.log', help="Path to log file")
    parser.add_argument('-b', '--backup', default=f'Backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}', help="Backup directory")
    parser.add_argument('-d', '--dry-run', action='store_true', help="Perform a dry run")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode")
    parser.add_argument('-f', '--force', action='store_true', help="Force scan even if file was processed before")
    parser.add_argument('-i', '--interactive', action='store_true', help="Interactive mode to confirm each substitution")
    parser.add_argument('--tail', type=int, default=10, help="Show last N processed files")
    parser.add_argument('--file-types', nargs='+', default=['.txt', '.md'], help="File types to process")

    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        sys.exit(1)

    script = SubstitutionScript(
        config_path=args.config,
        log_path=args.log,
        backup_dir=args.backup,
        dry_run=args.dry_run,
        verbose=args.verbose,
        force_scan=args.force,
        interactive=args.interactive,
        file_types=args.file_types
    )

    script.run(args.target)

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print(Fore.RED + "This script requires Python 3.10 or higher.")
        sys.exit(1)
    main()