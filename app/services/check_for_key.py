import json

def check_missing_type(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    def recursive_check(node, path=""):
        if isinstance(node, dict):
            if 'type' not in node:
                print(f"Missing 'type' key at path: {path}")
            for key, value in node.items():
                recursive_check(value, path + '/' + key if path else key)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                recursive_check(item, path + f"[{i}]")

    recursive_check(data)

json_file_path = './filtered_analysis_result.json'  # Replace with your JSON file path
check_missing_type(json_file_path)
