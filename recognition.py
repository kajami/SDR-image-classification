import tensorflow as tf
import os
import cv2
import imghdr
import numpy as np
from matplotlib import pyplot as plt
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten
from keras.metrics import Precision, Recall, BinaryAccuracy

# Limit the use of GPU Memory because it can cause out of memory errors.
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus: 
    tf.config.experimental.set_memory_growth(gpu, True)

#Making sure that images are in right format
data_dir = 'data\images' 
image_extensions = ['jpeg','jpg', 'bmp', 'png']

#1. Loop image folders
#2. Loop every single file in image folders
#3. Check if the file is valid image with valid extension
for image_class in os.listdir(data_dir): 
    for image in os.listdir(os.path.join(data_dir, image_class)):
        image_path = os.path.join(data_dir, image_class, image)
        try: 
            img = cv2.imread(image_path)
            tip = imghdr.what(image_path)
            if tip not in image_extensions: 
                print('Image not in extension list {}'.format(image_path))
        except Exception as e: 
            print('Issue with image {}'.format(image_path))
    
#This builds image dataset. Resizes images etc. Batch size is 10 because of small dataset, default value is 32.
data = tf.keras.utils.image_dataset_from_directory('data\images', batch_size=10)
#Allow access to data pipeline
data_iterator = data.as_numpy_iterator()
#Get a batch from iterator
batch = data_iterator.next()

#Show class number
#1 = nosignal 0 = signal
fig, ax = plt.subplots(ncols=4, figsize=(20,20))
for idx, img in enumerate(batch[0][:4]):
    ax[idx].imshow(img.astype(int))
    ax[idx].title.set_text(batch[1][idx])

#Scale data for optimization. We want values between 0.0-1.0.
scaled_data = data.map(lambda x,y: (x/255, y))
scaled_iterator = scaled_data.as_numpy_iterator()
scaled_batch = scaled_iterator.next()

#Set how many batches are going for each step
train_size = int(len(scaled_data)*.7)
val_size = int(len(scaled_data)*.2)+1
test_size = int(len(scaled_data)*.1)+1

train = scaled_data.take(train_size)
val = scaled_data.skip(train_size).take(val_size)
test = scaled_data.skip(train_size+val_size).take(test_size)

#Adding model, layers and optimizer
model = Sequential()

model.add(Conv2D(16, (3,3), 1, activation='relu', input_shape=(256,256,3)))
model.add(MaxPooling2D())
model.add(Conv2D(32, (3,3), 1, activation='relu'))
model.add(MaxPooling2D())
model.add(Conv2D(16, (3,3), 1, activation='relu'))
model.add(MaxPooling2D())
model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.compile('adam', loss=tf.losses.BinaryCrossentropy(), metrics=['accuracy'])

#Train the model. Add training logs. 
logdir='logs'
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)
history = model.fit(train, epochs=20, validation_data=val, callbacks=[tensorboard_callback])

#Show development of accuracy
fig = plt.figure()
plt.plot(history.history['accuracy'], color='teal', label='accuracy')
plt.plot(history.history['val_accuracy'], color='orange', label='validation accuracy')
fig.suptitle('Accuracy', fontsize=20)
plt.legend(loc="center right")
plt.show()

#Evaluate performance
pre = Precision()
re = Recall()
acc = BinaryAccuracy()

for batch in test.as_numpy_iterator(): 
    X, y = batch
    yhat = model.predict(X)
    pre.update_state(y, yhat)
    re.update_state(y, yhat)
    acc.update_state(y, yhat)

print(f'Precision: {pre.result().numpy()}, Recall: {re.result().numpy()}, Accuracy{acc.result().numpy()}')

#Test with own images
amimg = cv2.imread('test_data/am4.png')
colorimg = cv2.cvtColor(amimg, cv2.COLOR_BGR2RGB)
resize = tf.image.resize(colorimg, (256,256))
plt.imshow(resize.numpy().astype(int))
plt.show()

yhat = model.predict(np.expand_dims(resize/255, 0))
print(yhat)

if yhat > 0.5: 
    print(f'Image has no signal')
else:
    print(f'Image has signal')

#Saving model 
#model.save(os.path.join('models','imageclassifier.h5'))

#How to load and use the saved model
from keras.models import load_model
new_model = load_model(os.path.join('models','imageclassifier.h5'))
yhat2 = new_model.predict(np.expand_dims(resize/255, 0))