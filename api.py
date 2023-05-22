from flask import Flask, request, jsonify
import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

# Define the necessary variables
BASE_DIR = 'D:/Image Caption Generator/Flicker8k_Dataset'
WORKING_DIR = 'D:/Image Caption Generator'

# Load the pre-trained model
model = load_model(os.path.join(WORKING_DIR, 'best_model.h5'))

# Load the features from file
features = np.load(os.path.join(WORKING_DIR, 'features.npy'), allow_pickle=True).item()

# Load the tokenizer
with open(os.path.join(WORKING_DIR, 'tokenizer.pkl'), 'rb') as f:
    tokenizer = pickle.load(f)

# Define the maximum length of captions
max_length = 34

# Initialize Flask application
app = Flask(__name__)

# Define route for generating captions
@app.route('/generate_caption', methods=['POST'])
def generate_caption():
    # Check if image_id was provided in the request
    if 'image_id' not in request.json:
        return jsonify({'error': 'No image ID provided.'}), 400

    image_id = request.json['image_id']

    # Call the generate_caption_helper function with the image ID
    predicted_caption = generate_caption_helper(image_id)
    response = {'caption': predicted_caption}

    return jsonify(response), 200

def generate_caption_helper(image_id):
    # Load the image
    img_path = os.path.join(BASE_DIR, f"{image_id}.jpg")
    image = load_image(img_path)

    if image is not None:
        # Display the image
        plt.imshow(image)
        plt.axis('off')
        plt.show()

        # Predict the caption
        feature = features[image_id]
        feature = feature.reshape((1, 4096))
        in_text = 'startseq'
        for _ in range(max_length):
            sequence = tokenizer.texts_to_sequences([in_text])[0]
            sequence = pad_sequences([sequence], maxlen=max_length+1)  # Add +1 to match the model's input shape
            yhat = model.predict([feature, sequence], verbose=0)
            yhat = np.argmax(yhat)
            word = tokenizer.index_word[yhat]
            in_text += ' ' + word
            if word == 'endseq':
                break

        # Remove start and end tags from the predicted caption
        predicted_caption = in_text.split()[1:-1]
        predicted_caption = ' '.join(predicted_caption)

        return predicted_caption
    else:
        return 'Image not found.'

def load_image(img_path, target_size=(224, 224)):
    try:
        image = Image.open(img_path).convert('RGB')
        image = image.resize(target_size)
        return image
    except Exception as e:
        print(f"Error loading image: {img_path}")
        print(e)
        return None

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
