### {'$ref': '#/texts/213'}

| Experiment/ Simulation | Parameters | Values |
| --- | --- | --- |
| LoRa (Experiment) | Distance Frequency Bandwidth Coding Rate Spreading Factor MCU End Node LoRa radio chip MCU gateway LoRa radio chip | 1 m , 15 m , 30 m 868.0, 869.0, 870.0MHz 125 kHz 4/5 7 Heltec WiFi LoRa 32 (V3) SX1262 Adafruit Feather M0 SX1276 |
| TinyML (Simulation & experiment) | library model Data size | tensorflow → tensorflow.keras TensorFlowLite ESP32.h Sequential: Dense(10) Dense(10, regularizer=L1) Dense(F, activ.='softmax') optimizer=Adam 5000 for 1 end-node |
| Collaborative filtering (Simulation) | library Number of plants Number of soils | scikit-learn → cosine similarity 100 22013 |
| Plant recommender (Simulation) | Model library Number of soils Number of plants test size data | scikit-learn 22013 100 20 % |
