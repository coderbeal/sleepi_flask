from flask import Flask, request, redirect, url_for, send_file, render_template, jsonify
from PIL import Image
import os
import urllib.parse

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify(image_url=url_for('uploaded_file', filename=file.filename))
    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/process', methods=['POST'])
def process_image():
    data = request.get_json()
    filename = data['filename']
    filename = urllib.parse.unquote(filename)  # Decode the filename
    offsetX = data['offsetX']
    offsetY = data['offsetY']
    width = data['width']
    height = data['height']
    rotation = data['rotation']
    
    uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    sleepi_image_path = 'static/sleepi.png'

    try:
        with Image.open(uploaded_image_path) as base_img:
            base_img = base_img.convert('RGBA')  # Ensure base image has an alpha channel
            print("Base image mode:", base_img.mode, "Size:", base_img.size)

            with Image.open(sleepi_image_path) as sleepi_img:
                # Rescale sleepi_img based on the user input
                sleepi_img = sleepi_img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
                print("Resized sleepi image to:", sleepi_img.size)

                # Ensure sleepi_img has an alpha channel for transparency
                if sleepi_img.mode != 'RGBA':
                    sleepi_img = sleepi_img.convert('RGBA')
                print("Sleepi image mode after conversion:", sleepi_img.mode)

                # Rotate the sleepi image
                sleepi_img = sleepi_img.rotate(-int(rotation), expand=True, resample=Image.Resampling.BICUBIC)
                print(f"Rotated sleepi image by {rotation} degrees")

                # Create a new image for the final composite with the same mode and size as base_img
                final_img = Image.new('RGBA', base_img.size)
                final_img.paste(base_img, (0, 0))
                print("Base image pasted onto final image.")

                # Calculate the correct position on the final image
                final_offsetX = int(offsetX - sleepi_img.width / 2)
                final_offsetY = int(offsetY - sleepi_img.height / 2)
                print(f"Calculated final offsets: {final_offsetX}, {final_offsetY}")

                # Paste the sleepi_img onto the final_img at the specified position
                final_img.paste(sleepi_img, (final_offsetX, final_offsetY), mask=sleepi_img)
                print("Sleepi image pasted onto final image at position:", (final_offsetX, final_offsetY))

                # Convert final_img back to 'RGB' mode before saving as PNG
                final_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'final_' + filename)
                final_img.convert('RGB').save(final_image_path, format='PNG')
                print("Final image saved.")

    except Exception as e:
        print("Error processing image:", e)
        return jsonify({"error": str(e)}), 500

    return send_file(final_image_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
