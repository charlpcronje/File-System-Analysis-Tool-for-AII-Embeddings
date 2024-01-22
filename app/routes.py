from flask import Blueprint, request, jsonify
from .services.analyzer import traverse_directory

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome to the File System Analysis Tool!'})

@main.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        directory_path = data.get('directory_path')

        if directory_path and os.path.isdir(directory_path):
            analysis_result = traverse_directory(directory_path)
            return jsonify(analysis_result)
        else:
            return jsonify({'error': 'Invalid or non-existent directory path'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
