import numpy as np
import os
import requests
from flask import Flask, json, request, jsonify, render_template, Response, send_file
from io import BytesIO
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
import base64
import jsonpickle

import torch
from network.Transformer import Transformer
from cartoonize import transform

app = Flask(__name__)
app.config['UPLOAD_EXTENSIONS'] = ['jpg', 'png', 'jpeg', "jpg"]
app.config['UPLOAD_FOLDER'] = "samples"

# Note that there is only one available cartoonization style in this repo
style = 'Hosoda'
model = Transformer()
model.load_state_dict(torch.load(os.path.join("pretrained_model", style + "_net_G_float.pth")))
model.eval()


def validate(url):
    filename = url.split("/")[-1]
    res = filename.split('.')[-1]
    if res not in app.config["UPLOAD_EXTENSIONS"]:
        return None
    return filename


def edge_detection(path, thresh1, thresh2):
    #img = cv2.imread(path, 0)
    img = np.uint8(path)
    img = cv2.blur(img, (3, 3))
    canny = cv2.Canny(img, thresh1, thresh2)
    return canny


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html', img_in=None, img_out=None)
# test link https://i.ytimg.com/vi/hIRjlG-gbuI/maxresdefault.jpg


@app.route('/edge', methods=['POST'])
def make_edge():
    thr_hi = int(request.form['uthresh'])
    thr_low = int(request.form['lthresh'])
    url = request.form.get('url', None)
    
    # Collect input image
    if url:
        filename = validate(url)
        print(filename)
        cap = cv2.VideoCapture(url)
        ret, img = cap.read()
    else:
        file = request.files['image']
        filename = secure_filename(file.filename)
        fpath = app.config["UPLOAD_FOLDER"]+'/original.jpg'#+os.path.splitext(image.filename)[1]
        file.save(fpath)
        img = cv2.imread(fpath)

    # Perform Edge detection
    if img is not None:
        out = edge_detection(img, thr_hi, thr_low)
        out_name = "out_" + filename
        outpath = os.path.join(
            os.getcwd(), app.config['UPLOAD_FOLDER'], out_name)
        cv2.imwrite(outpath, out)

        out = Image.fromarray(out)
        fileobj = BytesIO()
        out.save(fileobj, "PNG", quality = 300)
        fileobj.seek(0)

        return send_file(fileobj, mimetype="image/PNG")

    return Response(
        response= jsonpickle.encode({"error": "Invalid file input"}),
         status=404, mimetype="application/json")


@app.route('/cartoonize', methods=['POST'])
def make_cartoon():
    
    file = request.files['image']

    if file is not None:
        out = transform(model, file)

        fileobj = BytesIO()
        out.save(fileobj, "PNG", quality = 100)
        fileobj.seek(0)
        return send_file(fileobj, mimetype="image/PNG")

    return Response(response= jsonpickle.encode({"error": "Invalid file input"}), status=404, mimetype="application/json")

    

if __name__ == '__main__':
    app.run(debug= True)
