# -*- coding: utf-8 -*-
"""probabilistic Bayesian neural network.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bgcgIs6gZ8zBOvagL_SS21PyWPmE0659
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow_datasets as tfds
import tensorflow_probability as tfp
from tensorflow.keras.layers import *

# Define the prior weight distribution as Normal of mean=0 and stddev=1.
# Note that, in this example, the we prior distribution is not trainable,
# as we fix its parameters.
def _prior(kernel_size, bias_size, dtype=None):
    n = kernel_size + bias_size
    prior_model = keras.Sequential(
        [
            tfp.layers.DistributionLambda(
                lambda t: tfp.distributions.MultivariateNormalDiag(
                    loc=tf.zeros(n), scale_diag=tf.ones(n)
                )
            )
        ]
    )
    return prior_model


# Define variational posterior weight distribution as multivariate Gaussian.
# Note that the learnable parameters for this distribution are the means,
# variances, and covariances.
def _posterior(kernel_size, bias_size, dtype=None):
    n = kernel_size + bias_size
    posterior_model = keras.Sequential(
        [
            tfp.layers.VariableLayer(
                tfp.layers.MultivariateNormalTriL.params_size(n), dtype=dtype
            ),
            tfp.layers.MultivariateNormalTriL(n),
        ]
    )
    return posterior_model



def _negative_loglikelihood(targets, estimated_distribution):
    return -estimated_distribution.log_prob(targets)


def modelFit(train_size,input_length,lr,X,Y,validation_split=0,epochs=1):
    '''
    train_size: the size of the training set; int
    input_length: the dimension of one trainig example; int
    lr: learning rate; float
    X: training examples; nparray
    Y: labels
    validation_split: ratio to split from (X,Y) as validation set
    epochs: number of epochs; int
    '''

    tf.keras.backend.clear_session()

    inputs = Input(shape=(input_length,))
    x = BatchNormalization()(inputs)
    x = tfp.layers.DenseVariational(units=8,make_prior_fn=_prior,make_posterior_fn=_posterior,kl_weight=1 / train_size,activation='sigmoid')(x)
    x = tfp.layers.DenseVariational(units=8,make_prior_fn=_prior,make_posterior_fn=_posterior,kl_weight=1 / train_size,activation='sigmoid')(x)
    distribution_params = layers.Dense(units=2)(x)
    outputs = tfp.layers.IndependentNormal(1)(distribution_params)


    model = tf.keras.Model(inputs=inputs,outputs=outputs)

    model.compile(
        optimizer=keras.optimizers.RMSprop(learning_rate=lr),
        loss=_negative_loglikelihood,
        metrics=[keras.metrics.RootMeanSquaredError()],
    )

    model.fit(x=X,y=Y,epochs=epochs,validation_split=validation_split)
    return model



def modelPredict(trained_model,X):
    prediction_distribution = trained_model(X)
    prediction_mean = prediction_distribution.mean().numpy().tolist()
    prediction_stdv = prediction_distribution.stddev().numpy()

    return prediction_mean,prediction_stdv