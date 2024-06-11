from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'image_url': f'/uploads/{filename}'}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process', methods=['POST'])
def process_image():
    data = request.json
    filename = data['filename']
    offsetX = data['offsetX']
    offsetY = data['offsetY']
    width = data['width']
    height = data['height']
    rotation = data['rotation']

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    sleepi_path = os.path.join('static', 'sleepi.png')

    try:
        with Image.open(image_path) as img:
            with Image.open(sleepi_path) as sleepi:
                sleepi = sleepi.resize((int(width), int(height)))
                sleepi = sleepi.rotate(float(rotation), expand=True)
                
                # Convert offsets to integers for pasting
                offsetX = int(offsetX)
                offsetY = int(offsetY)

                img.paste(sleepi, (offsetX, offsetY), sleepi)

            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'final_image.png')
            img.save(output_path)

        return send_file(output_path, as_attachment=True, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
