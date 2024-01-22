# analyzer.py

import os
import hashlib
import time
import json
from dotenv import load_dotenv
import sys

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.getcwd())
sys.path.append(parent_dir)
# Load environment variables
from utils.logger import log

load_dotenv()

base_path = os.getenv('BASE_PATH', '')

# Get indexed and non indexed file extensions and folders from .env
indexed_extensions = os.getenv('INDEX_FILE_EXTENSIONS', '').split(',')
excluded_file_types = os.getenv('EXCLUDED_FILE_TYPES', '').split(',')
excluded_folders = [os.path.join(base_path, folder) for folder in os.getenv('EXCLUDED_FOLDERS', '').split(',')]

def should_analyze(path):
    """
    Determine if the given path should be analyzed based on configuration.
    """
    # Convert path to absolute path
    absolute_path = os.path.abspath(path)

    # Check if the file is in an excluded folder
    for folder in excluded_folders:
        if absolute_path.startswith(folder):
            return False

    # Check if the file type is excluded
    file_ext = os.path.splitext(path)[1]
    if file_ext in excluded_file_types:
        return False

    # Check if the file's extension is in the list of indexed extensions
    return file_ext in indexed_extensions

def file_type(filepath):
    """
    Determine if the given path should be analyzed based on configuration.
    """
    # Check if the file is in an excluded folder
    for folder in excluded_folders:
        if folder in path:
            return False

    # Check if the file type is excluded
    for file_type in excluded_file_types:
        if file_type in path:
            return False

    # Check if the file's extension is in the list of indexed extensions
    ext = file_extension(path)
    return ext in indexed_extensions

def count_lines_words_tokens(file_path):
    """
    Counts lines, words, and tokens in a file.
    """
    lines = words = tokens = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                lines += 1
                words += len(line.split())
                tokens += len(line)  # Simplistic token count
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return lines, words, tokens

def file_metadata(filepath):
    """
    Returns metadata for the specified file, including line, word, and token counts.
    """
    size = os.path.getsize(filepath)
    created_at = time.ctime(os.path.getctime(filepath))  
    modified_at = time.ctime(os.path.getmtime(filepath))  
    file_extension = os.path.splitext(filepath)[1]

    file_hash = ''
    try:
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Error reading file for hash {filepath}: {e}")

    lines, words, tokens = count_lines_words_tokens(filepath)

    return {
        'size': size,
        'created_at': created_at,
        'modified_at': modified_at,
        'file_extension': file_extension,
        'hash': file_hash,
        'lines_of_code': lines,
        'word_count': words,
        'token_count': tokens
    }

def aggregate_metadata(contents):
    """
    Aggregates metadata for a directory based on its contents.
    """
    total_lines = total_words = total_tokens = 0
    for item in contents.values():

        if item['type'] == 'file':
            total_lines += item['metadata']['lines_of_code']
            total_words += item['metadata']['word_count']
            total_tokens += item['metadata']['token_count']
        elif item['type'] == 'directory':
            dir_lines, dir_words, dir_tokens = aggregate_metadata(item['contents'])
            total_lines += dir_lines
            total_words += dir_words
            total_tokens += dir_tokens

    return total_lines, total_words, total_tokens

def traverse_directory(path, base_path="", index_data=None, is_filtered=False):
    """
    Traverses directories and files, collecting metadata, and adding path information.
    """
    tree = {}
    # Ensure that absolute_base_path is correctly defined
    absolute_base_path = os.path.abspath(base_path if base_path else path)
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            log(f"Processing entry: {entry}, full path: {full_path}", level='DEBUG')
            
            relative_path = os.path.relpath(full_path, absolute_base_path)

            # Skip if should not analyze
            if not should_analyze(full_path):
                continue

            is_indexed = index_data.get(full_path, True) if index_data else True
            if is_filtered and not is_indexed:
                continue

            if os.path.isdir(full_path):
                contents = traverse_directory(full_path, base_path, index_data, is_filtered)
                total_lines, total_words, total_tokens = aggregate_metadata(contents)
                tree[entry] = {
                    'type': 'directory',
                    'absolute_path': full_path,
                    'relative_path': relative_path,
                    'index': is_indexed,
                    'module_name': entry, 
                    'is_module': False, 
                    'contents': contents,
                    'total_lines_of_code': total_lines,
                    'total_word_count': total_words,
                    'total_token_count': total_tokens
                }
            else:
                tree[entry] = {
                    'type': 'file',
                    'index': is_indexed,
                    'metadata': file_metadata(full_path),
                    'absolute_path': full_path,
                    'relative_path': relative_path
                }
    except PermissionError as e:
        print(f'Permission denied for {path}: {e}')
    except Exception as e:
        print(f"Error processing directory {path}: {e}")

    return tree

def verify_aggregated_counts(json_file, report_file='error_analysis_report.md'):
    with open(json_file, 'r') as file:
        data = json.load(file)

    def format_counts(counts):
        lines = counts.get('lines_of_code', 'N/A')
        words = counts.get('word_count', 'N/A')
        tokens = counts.get('token_count', 'N/A')
        return f"Lines: {lines}, Words: {words}, Tokens: {tokens}"

    def verify_folder(folder_data, base_path=""):
        for name, item in folder_data.items():
            log(f"Verifying item: {name} in {base_path}", level='DEBUG')

            # If 'type' key is missing, skip this item
            if 'type' not in item:
                log(f"Skipping item with missing 'type' key: {name} in {base_path}", level='WARNING')
                continue

            if item['type'] == 'directory':
                # Re-analyze the directory if necessary
                totals = analyze_directory(item['absolute_path'], only_totals=True)
                expected_totals = {
                    'lines_of_code': item['total_lines_of_code'],
                    'word_count': item['total_word_count'],
                    'token_count': item['total_token_count']
                }

                # Check for discrepancies
                if totals != expected_totals:
                    with open(report_file, 'a') as report:
                        report.write(f"- **{item['relative_path']}**:\n")
                        report.write(f"  - Expected: {format_counts(expected_totals)}\n")
                        report.write(f"  - Found: {format_counts(totals)}\n")
                        discrepancy = {
                            'lines_of_code': expected_totals['lines_of_code'] - totals['lines_of_code'],
                            'word_count': expected_totals['word_count'] - totals['word_count'],
                            'token_count': expected_totals['token_count'] - totals['token_count']
                        }
                        report.write(f"  - Discrepancy: {format_counts(discrepancy)}\n\n---\n\n")
                verify_folder(item['contents'], item['absolute_path'])

    with open(report_file, 'w') as report:
        report.write("# Error Analysis Log\n\n")

    verify_folder(data)

    print(f"Error analysis report generated: {report_file}")


def format_counts(counts):
    lines = counts.get('lines_of_code', 'N/A')
    words = counts.get('word_count', 'N/A')
    tokens = counts.get('token_count', 'N/A')
    return f"Lines: {lines}, Words: {words}, Tokens: {tokens}"

def analyze_directory(directory_path, index_file='index.json', module_file='modules.json', only_totals=False):
    """
    Analyze the directory, maintain index flags, and generate two reports.
    """
    # Load existing index data
    if os.path.isfile(index_file):
        with open(index_file, 'r') as file:
            index_data = json.load(file)
    else:
        index_data = {}

    analysis_result = traverse_directory(directory_path, index_data)

    # Save analysis result with index flags
    with open('analysis_result.json', 'w') as file:
        json.dump(analysis_result, file, indent=4)

    # Create a filtered analysis excluding non-indexed files/folders
    filtered_analysis_result = traverse_directory(directory_path, index_data, is_filtered=True)

    # Process modules
    modules_analysis = {}
    if os.path.isfile(module_file):
        with open(module_file, 'r') as file:
            module_paths = json.load(file).get('module_paths', [])
            for module_path in module_paths:
                modules_analysis[module_path] = traverse_directory(module_path, index_data)

    filtered_analysis_result['modules'] = modules_analysis

    # Save filtered analysis result
    with open('filtered_analysis_result.json', 'w') as file:
        json.dump(filtered_analysis_result, file, indent=4)

    # Only generate verification report at the top level call, not during recursion
    if not only_totals:
        verify_aggregated_counts('filtered_analysis_result.json')

    return filtered_analysis_result  # Return only the filtered result as it's the final desired outcome

def generate_ascii_tree(json_file, output_file='ascii_tree.txt'):
    with open(json_file, 'r') as file:
        data = json.load(file)

    def build_tree(node, prefix=""):
        tree_str = ""
        entries = list(node.items())
        for i, (name, item) in enumerate(entries):
            connector = "├── " if i < len(entries) - 1 else "└── "
            
            # Check if item is a directory or file and handle missing 'type' key
            item_type = item.get('type')
            if item_type == 'directory':
                # Aggregate metadata for directories
                lines = item.get('total_lines_of_code', 'N/A')
                words = item.get('total_word_count', 'N/A')
                tokens = item.get('total_token_count', 'N/A')
                tree_str += f"{prefix}{connector}{name}/ (Lines: {lines}, Words: {words}, Tokens: {tokens})\n"
                if 'contents' in item:
                    ext = "│   " if i < len(entries) - 1 else "    "
                    tree_str += build_tree(item['contents'], prefix + ext)
            elif item_type == 'file':
                # Metadata for files
                metadata = item.get('metadata', {})
                lines = metadata.get('lines_of_code', 'N/A')
                words = metadata.get('word_count', 'N/A')
                tokens = metadata.get('token_count', 'N/A')
                tree_str += f"{prefix}{connector}{name} (Lines: {lines}, Words: {words}, Tokens: {tokens})\n"
            else:
                # Handle case where 'type' key is missing
                print(f"Warning: 'type' key not found for item {name}")

        return tree_str

    ascii_tree = build_tree(data)

    with open(output_file, 'w') as file:
        file.write(ascii_tree)

    print(f"ASCII Tree written to {output_file}")


# Example usage
if __name__ == '__main__':
    directory_to_analyze = '/var/www/html/ignite'  # Replace with the directory you want to analyze
    analyze_directory(directory_to_analyze)
    generate_ascii_tree('filtered_analysis_result.json')

    