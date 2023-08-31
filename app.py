from flask import Flask, render_template, request, redirect, url_for, jsonify
import boto3
import os

app = Flask(__name__)

# AWS configuration from environment variables
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
BUCKET_NAME = 'my-flaskapp-bucket'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the S3 client with the provided AWS configurations.
s3 = boto3.client(
    's3',
    region_name='us-east-2',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']

    if file.filename == '':
        return 'No selected file'
    
    if not allowed_file(file.filename):
        return 'File type not allowed'
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    try:
        with open(file_path, "rb") as f:
            s3.upload_fileobj(f, BUCKET_NAME, file.filename)
        os.remove(file_path)  # Remove the local file after uploading to S3
    except Exception as e:
        return f"An error occurred: {e}"

    return redirect(url_for('list_files'))

@app.route('/files')
def list_files():
    try:
        files = s3.list_objects(Bucket=BUCKET_NAME)['Contents']
    except Exception as e:
        return f"An error occurred: {e}"
    return render_template('files.html', files=files)

@app.route('/files/<filename>/download-url', methods=['GET'])
def get_download_url(filename):
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600
        )
    except Exception as e:
        return f"An error occurred: {e}"
    return jsonify({'url': url})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

