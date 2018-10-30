from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
import numpy as np


class Network_gpu(object):
    # this class is engined with keras package, which is expected to be more
    # powerful
    def __init__(self):
        self.model = Sequential()
        self.model.add(Dense(22, kernel_initializer='uniform', activation='relu'))
        self.model.add(Dense(30, kernel_initializer='uniform', activation='relu'))
        self.model.add(Dense(2, kernel_initializer='uniform', activation='sigmoid'))
        self.x = []
        self.y = []
        # Compile model
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def fetch_state(self, Memory):
        x, y = Memory
        self.x.append(x)
        self.x.append(y)
        return

    def feedforward(self, state):
        # with the state input, compare different action and return the argmax action
        # q_value = []
        # for a in range(2):
        #     q_value.append(model.predict(state+[i]))
        # return np.argmax(q_value)
        return self.model.predict(state)

    def get_action(self, cur_state):
        q_values = []
        for i in range(2):
            q_values.append(self.feedforward(state+[i]))
        # print('Q values:', q_values)
        return np.argmax(q_values)

    def SGD(self):
        self.model.fit(self.x, self.y, epochs=1, batch_size=100,  verbose=2)
        return

    def save(self, num_epoch):
        model_json = self.model.to_json()
        with open('./dql_train/keras_model_%d.json' % num_epoch, "w") as json_file:
            json_file.write(model_json)
        # serialize weights to HDF5
        self.model.save_weights('./dql_train/keras_model_%d.h5' % num_epoch)
        # print("Saved model to disk")
        return

    def load(self, filename1, filename2):
        # load json and create model
        json_file = open(filename1, 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = model_from_json(loaded_model_json)
        # load weights into new model
        self.model.load_weights(filename2)
        # compile model
        self.model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
        return
