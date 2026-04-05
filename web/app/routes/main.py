from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/archive')
def archive_page():
    return render_template('archive.html')

@main_bp.route('/api/archive/list', methods=['GET'])
def get_archive_list():
    return jsonify({"items": []})