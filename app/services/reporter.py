# reporter.py
def generate_report(analysis_result):
    """
    Generates a detailed report from the analysis results.
    """
    report = {
        'total_lines_of_code': 0,
        'total_words': 0,
        'total_tokens': 0,
        'module_details': {}
    }

    def process_node(node, path):
        if node.get('is_module'):
            report['module_details'][path] = {
                'lines_of_code': 0, 'words': 0, 'tokens': 0
            }

        for name, content in node.get('contents', {}).items():
            new_path = os.path.join(path, name)
            if 'file_size' in content:  # It's a file
                report['total_lines_of_code'] += content.get('lines_of_code', 0)
                report['total_words'] += content.get('word_count', 0)
                report['total_tokens'] += content.get('token_count', 0)

                if node.get('is_module'):
                    report['module_details'][path]['lines_of_code'] += content.get('lines_of_code', 0)
                    report['module_details'][path]['words'] += content.get('word_count', 0)
                    report['module_details'][path]['tokens'] += content.get('token_count', 0)
            else:
                process_node(content, new_path)

    for root, tree in analysis_result.items():
        process_node(tree, root)

    return report
