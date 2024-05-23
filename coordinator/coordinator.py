import pika
import sys
import os
import json

import hashlib

import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename


# in_dir = os.environ['IN_DIR']
# out_dir = os.environ['OUT_DIR']
in_dir = "/app/in"
out_dir = "/app/out"

ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = in_dir
app.config['OUTPUT_FOLDER'] = out_dir

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # data = json.loads(request.form.get('data'))
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                data = f.read()
                filesha = hashlib.sha256(data).hexdigest()

            rabbitconn = pika.BlockingConnection(
                pika.ConnectionParameters('rabbitmq'))
            channel = rabbitconn.channel()
            channel.queue_declare(queue='parse_pdf')
            rabbit_data = {
                "id": filesha,
                "in_path": os.path.join(app.config['UPLOAD_FOLDER'], filename),
                "out_path": os.path.join(app.config['UPLOAD_FOLDER'], f'{filesha}.md'),
                "status": "unprocessed"
            }

            channel.basic_publish(exchange='',
                                  routing_key='parse_pdf',
                                  body=json.dumps(rabbit_data))
            channel.close()
            return "success"

        return "failure"

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=True)
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    finally:
        sys.exit(0)
