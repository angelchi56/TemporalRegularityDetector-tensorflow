import tensorflow as tf
from ops import conv2d, deconv2d

# CHECK 
reg_weight = 0.01

class FullyConvolutionalAutoencoder(object):
  def __init__(self, sess, input_shape):
    """Fully convolutional autoencoder for temporal-
    regularity detection. 

    Args:
      sess : TensorFlow session
      input_shape : Shape of the input data. [n, h, w, c]
    """
    self._sess = sess
    self._input_shape = input_shape

    self._x = tf.placeholder(tf.float32, self._input_shape)

    self._var_list = []
    self._build() 

    self._saver = tf.train.Saver(self._var_list)
    self._sess.run(tf.initialize_all_variables())

  def _build(self):
    conv_h1 = self._conv2d(self._x, 512, 11, 11, 4, 4, "conv_h1")
    conv_h2 = self._conv2d(conv_h1, 512, 2, 2, 2, 2, "conv_h2") 
    conv_h3 = self._conv2d(conv_h2, 256, 5, 5, 1, 1, "conv_h3")
    conv_h4 = self._conv2d(conv_h3, 256, 2, 2, 2, 2, "conv_h4") 
    conv_h5 = self._conv2d(conv_h4, 128, 3, 3, 1, 1, "conv_h5")

    output_shape5 = tf.pack([conv_h5.get_shape()[:3], 128])
    output_shape4 = tf.pack([conv_h4.get_shape()[:3], 128])
    output_shape3 = tf.pack([conv_h3.get_shape()[:3], 256])
    output_shape2 = tf.pack([conv_h2.get_shape()[:3], 256])
    output_shape1 = tf.pack([conv_h1.get_shape()[:3], 512])

    deconv_h5 = self._deconv2d(conv_h5, output_shape5, 
                               3, 3, 1, 1, "deconv_h5")
    deconv_h4 = self._deconv2d(deconv_h5, output_shape4, 
                               2, 2, 2, 2, "deconv_h4")
    deconv_h3 = self._deconv2d(deconv_h4, output_shape3, 
                               3, 3, 1, 1, "deconv_h3")
    deconv_h2 = self._deconv2d(deconv_h3, output_shape2, 
                               2, 2, 2, 2, "deconv_h2")
    deconv_h1 = self._deconv2d(deconv_h2, output_shape1, 
                               5, 5, 1, 1, "deconv_h1")
    self._y = self._deconv2d(deconv_h1, self._x.get_shape(), 
                               11, 11, 4, 4, "output")

    self._reconstruct_loss = \
      tf.nn.l2_loss(self._x - self._y) / self._x.get_shape()[0]
    self._regularize_loss = \
      reg_weight * 2. * tf.nn.l2_loss(tf.pack(
        [var for var in self._var_list if 'conv2d' in var.name]))

    self._loss = self._reconstruct_loss + self._regularize_loss
    self._train = tf.train.AdamOptimizer(1e-4).minimize(
      self._loss, var_list=self._var_list)

    self._pixel_error = tf.reduce_sum(
      tf.square(self._x-self._y), [1,2,3])
    pixel_error_max = tf.reduce_max(self_pixel_error)
    pixel_error_min = tf.reduce_min(self_pixel_error)

    self._regularity = \
      1. - (self._pixel_error - pixel_error_max) / pixel_error_min

  def save(self, ckpt_path):
    self._saver.save(self._sess, ckpt_path)

  def load(self, ckpt_path):
    self._saver.restore(self._sess, ckpt_path)

  def fit(self, input_):
    # CHECK
    _, rec_loss, reg_loss = self._sess.run(
      [self._train, self._reconstruct_loss, self._regularize_loss],
      {self._x:input_})
    print(" reconstruct_loss : {:09f}\tregularize_loss : {:09f}".format(rec_loss, reg_loss))

  def reconstruct(self, input_):
    return self._sess.run(self._y, {self._x:input_})

  def get_regularity(self, inputs_):
    return self._sess.run(self._regularity, {self._x:input_})

  def _conv2d(input_, output_dim, 
             k_h=3, k_w=3, s_h=2, s_w=2,
             name, stddev=0.01):
    with tf.variable_cope(name):
      k = tf.get_variable('conv2d', 
        [k_h, k_w, input_.get_shape()[-1], output_dim],
        initializer=tf.truncated_normal_initializer(stddev=stddev))
      conv = tf.nn.conv2d(input_, k, [1, s_h, s_w, 1], "VALID")

      b = tf.get_variable('biases', [1, 1, 1, output_dim],
        initializer=tf.constant_initializer(0.0)

      self._var_list.append(k)
      self._var_list.append(b)
    return conv + b

  def _deconv2d(input_, output_shape,
                k_h=3, k_w=3, s_h=2, s_w=2,
                name, stddev=0.01):
    with tf.variable_cope(name):
      k = tf.get_variable('deconv2d',
        [k_h, k_w, output_shape[-1], input_.get_shape()[-1]],
        initializer=tf.random_normal_initializer(stddev=stddev))
      deconv = tf.nn.conv2d_transpose(input_, k, [1, s_h, s_w, 1], "VALID")

      b = tf.get_variable('biases', [1, 1, 1, output_shape[-1]],
        initializer=tf.constant_initializer(0.0))

      self._var_list.append(k)
      self._var_list.append(b)
    return deconv + b