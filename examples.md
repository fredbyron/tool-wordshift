# Basic usage
python3 app.py filename.txt

# Specify a directory
python3 app.py /path/to/directory

# Force scan
python3 app.py filename.txt -f

# Dry run
python3 app.py filename.txt -d

# Verbose mode
python3 app.py filename.txt -v

# Interactive mode
python3 app.py filename.txt -i

# Custom log file path
python3 app.py filename.txt -l custom_log.log

# Show last 20 processed files
python3 app.py --tail 20