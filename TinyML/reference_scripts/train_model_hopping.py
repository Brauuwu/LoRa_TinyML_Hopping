# -*- coding: utf-8 -*-
"""train_model_hooping.py
Author: Mounir Bensalem
Email: mounir.bensalem@tu-bs.de
Created on 
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Reading collected data associated to each channel
filename1 = "channel1.csv"
filename2 = "channel2.csv"
filename3 = "channel3.csv"

plt.rcParams["figure.figsize"] = (20,10)
headers = ['packet_ID','source','CH1', 'CH2', 'CH3',  'size_of_message','RSSI','SNR','frequency'] # ['CH1', 'CH2', 'CH3', 'SNR', 'RSSI', 'PacketSize', 'TimeSlot', 'usedCH']
#df1 = pd.read_csv(filename1, names=headers,  skiprows=1)
#df2 = pd.read_csv(filename2, names=headers,  skiprows=1)
#df3 = pd.read_csv(filename3, names=headers,  skiprows=1)

#print(df1.head(10))
#print(df2.head(10))
#print(df3.head(10))



import tensorflow as tf

SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

CHANNELS = ["868","869","870"]

SAMPLES_PER_CHANNEL = 10

NUM_CHANNELS = len(CHANNELS)

ONE_HOT_ENCODED_CHANNELS = np.eye(NUM_CHANNELS)

inputs = []
outputs = []

# read each csv file and push an input and output
for channel_index in range(NUM_CHANNELS):
  channel = CHANNELS[channel_index]
  print(f"Processing index {channel_index} for channel '{channel}'.")

  output = ONE_HOT_ENCODED_CHANNELS[channel_index]

  df = pd.read_csv("data/MLdataready/A/" + channel + ".csv",names = headers,  skiprows=1)

  # calculate the number of gesture recordings in the file
  num_recordings = int(df.shape[0] / SAMPLES_PER_CHANNEL)

  print(f"\tThere are {num_recordings} recordings of the {channel} channel.")

  for i in range(num_recordings):
    tensor = []
    for j in range(SAMPLES_PER_CHANNEL):
      index = i * SAMPLES_PER_CHANNEL + j
      tensor += [
          (df['CH1'][index])        ,
          (df['CH2'][index])        ,
          (df['CH3'][index])        ,
          (df['SNR'][index])        ,
          (df['RSSI'][index])       ,
          (df['size_of_message'][index]) ,
          (df['packet_ID'][index])   ,
          (df['frequency'][index])
      ]

    inputs.append(tensor)
    outputs.append(output)
inputs = np.array(inputs)
outputs = np.array(outputs)
print(inputs)

# Normalize or standardize the input data
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()  # You can use MinMaxScaler() as an alternative
inputs = scaler.fit_transform(inputs)

# Randomize the order of the inputs, so they can be evenly distributed for training, testing, and validation
num_inputs = len(inputs)
randomize = np.arange(num_inputs)
np.random.shuffle(randomize)

inputs = inputs[randomize]
outputs = outputs[randomize]

TRAIN_SPLIT = int(0.6 * num_inputs)
TEST_SPLIT = int(0.2 * num_inputs + TRAIN_SPLIT)

inputs_train, inputs_test, inputs_val = np.split(inputs, [TRAIN_SPLIT, TEST_SPLIT])
outputs_train, outputs_test, outputs_val = np.split(outputs, [TRAIN_SPLIT, TEST_SPLIT])

from tensorflow.keras import regularizers
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(10, activation='relu'))
model.add(tf.keras.layers.Dense(10, activation='relu',kernel_regularizer= regularizers.L1(l1=1e-4)))
#model.add(tf.keras.layers.Dropout(rate=0.2, noise_shape = (1, 60), seed = 1))
model.add(tf.keras.layers.Dense(NUM_CHANNELS, activation = 'softmax'))
model.compile(optimizer=tf.keras.optimizers.Adam(), loss='mse', metrics=['mae', 'accuracy'])
history = model.fit(inputs_train, outputs_train, epochs=500, batch_size=1, validation_data=(inputs_val, outputs_val))

plt.rcParams["figure.figsize"] = (20,10)

loss = history.history['loss']
val_loss = history.history['val_loss']
acc = history.history['accuracy']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, acc, 'g.', label='Training accuracy')
plt.plot(epochs, loss, 'r.', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
#plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Metrics')
plt.legend()
plt.show()

loss = history.history['loss']
val_loss = history.history['val_loss']
#acc = history.history['accuracy']
epochs = range(1, len(loss) + 1)
#plt.plot(epochs, acc, 'g.', label='Training accuracy')
plt.plot(epochs, loss, 'r.', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
#plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

#loss = history.history['loss']
#val_loss = history.history['val_loss']
acc = history.history['accuracy']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, acc, 'g.', label='Training accuracy')
#plt.plot(epochs, loss, 'r.', label='Training loss')
#plt.plot(epochs, val_loss, 'b', label='Validation loss')
#plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

SKIP = 20
plt.plot(epochs[SKIP:], loss[SKIP:], 'g.', label='Training loss')
plt.plot(epochs[SKIP:], val_loss[SKIP:], 'b', label='Validation loss')
#plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

mae = history.history['mae']
val_mae = history.history['val_mae']
plt.plot(epochs[SKIP:], mae[SKIP:], 'g.', label='Training MAE')
plt.plot(epochs[SKIP:], val_mae[SKIP:], 'b', label='Validation MAE')
#plt.title('Training and validation mean absolute error')
plt.xlabel('Epochs')
plt.ylabel('MAE')
plt.legend()
plt.show()

from tensorflow.keras import backend as K
def categorical_accuracy(y_true, y_pred):
    return K.mean(K.equal(K.argmax(y_true, axis=-1), K.argmax(y_pred, axis=-1)))

predictions = model.predict(inputs_test)

# print the predictions and the expected ouputs
print("predictions =\n", np.round(predictions, decimals=3))
print("actual =\n", outputs_test)

print("Accuracy: ",  history.history['accuracy'][K.argmin(history.history['loss'])])

# Plot the predictions along with to the test data
plt.clf()
plt.title('Training data predicted vs actual values')
#print(inputs_test)
#print(outputs_test)
print(len(inputs_test))
print(len(outputs_test))
#plt.plot(inputs_test, outputs_test, 'b.', label='Actual')
#plt.plot(inputs_test, predictions, 'r.', label='Predicted')
#plt.show()

# Save TF model
model.save('complete_TFmodel_ch_'+str(NUM_CHANNELS)+'.keras')

# Save weights to HDF5 format
model.save_weights('my_model_weights_ch_'+str(NUM_CHANNELS)+'.weights.h5')
model.save('complete_TFmodel_ch_'+str(NUM_CHANNELS)+'.h5')

# Convert the model to the TensorFlow Lite format without quantization
#!apt-get -qq install xxd
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the model to disk
open("channel_modelC.tflite", "wb").write(tflite_model)

import os
basic_model_size = os.path.getsize("channel_modelC.tflite")
print("Model is %d bytes" % basic_model_size)

#os.system()

import subprocess

# Write the start of the header file
with open("modelC.h", "w") as f:
    f.write('const unsigned char model[] = {\n')

# Append the binary content of the .tflite file converted to C array format
subprocess.run("cat channel_modelC.tflite | xxd -i >> modelC.h", shell=True, check=True)

# Finish the header file
with open("modelC.h", "a") as f:
    f.write('};\n')


import os
model_h_size = os.path.getsize("model.h")
print(f"Header file, modelC.h, is {model_h_size:,} bytes.")
print("\nOpen the side panel (refresh if needed). Double click modelC.h to download the file.")
