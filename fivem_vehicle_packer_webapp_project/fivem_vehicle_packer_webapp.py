
from flask import Flask, request, send_file, render_template_string
import zipfile
import shutil
from pathlib import Path
import os
import tempfile

app = Flask(__name__)

HTML_FORM = '''
<!doctype html>
<title>FiveM Vehicle Packer</title>
<h1>Upload a ZIP of Vehicle Folders</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=zipfile>
  <input type=submit value=Upload>
</form>
'''

def pack_vehicle_folder(vehicle_folder, export_folder):
    vehicle_path = Path(vehicle_folder)
    car_name = vehicle_path.name
    data_path = Path(export_folder) / "data" / car_name
    stream_path = Path(export_folder) / "stream" / car_name
    data_path.mkdir(parents=True, exist_ok=True)
    stream_path.mkdir(parents=True, exist_ok=True)

    for file in vehicle_path.rglob('*'):
        if file.is_file():
            ext = file.suffix.lower()
            if ext == ".meta":
                shutil.copy(file, data_path / file.name)
            elif ext in {".yft", ".ytd"} or file.name.lower().endswith("_hi.yft"):
                shutil.copy(file, stream_path / file.name)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "zipfile" not in request.files:
            return "No file part", 400
        file = request.files["zipfile"]
        if file.filename == "":
            return "No selected file", 400

        with tempfile.TemporaryDirectory() as tmpdir:
            upload_path = Path(tmpdir) / "upload"
            upload_path.mkdir()
            zip_path = upload_path / "vehicles.zip"
            file.save(zip_path)

            extract_dir = upload_path / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Process all subfolders
            for subfolder in extract_dir.iterdir():
                if subfolder.is_dir():
                    pack_vehicle_folder(subfolder, output_dir)

            result_zip = Path(tmpdir) / "packed_vehicles.zip"
            shutil.make_archive(result_zip.with_suffix(""), 'zip', output_dir)

            return send_file(result_zip, as_attachment=True)

    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    app.run(debug=True)
