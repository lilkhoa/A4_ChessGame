import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
import numpy as np

from .tensor_converter import TensorConverter

INPUT_SHAPE = (8, 8, 21)
NUM_FILTERS = 32
NUM_RESIDUAL_BLOCKS = 3
L2_CONST = 1e-3

# Hyperparameters
LEARNING_RATE = 0.0001
EPOCHS = 100
BATCH_SIZE = 128

def build_res_block(input_tensor, filters):
    """A Residual Block (ResBlock)"""
    shortcut = input_tensor
    
    x = layers.Conv2D(filters, 
                     kernel_size=(3, 3), 
                     padding='same', 
                     use_bias=False, 
                     kernel_regularizer=regularizers.l2(L2_CONST))(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    
    x = layers.Conv2D(filters, 
                     kernel_size=(3, 3), 
                     padding='same', 
                     use_bias=False, 
                     kernel_regularizer=regularizers.l2(L2_CONST))(x)
    x = layers.BatchNormalization()(x)
    
    x = layers.add([shortcut, x])
    x = layers.ReLU()(x)
    
    return x


def build_chess_model(input_shape=INPUT_SHAPE, 
                      num_filters=NUM_FILTERS, num_residual_blocks=NUM_RESIDUAL_BLOCKS):
    """
    Build a value-only neural network for ML + Minimax architecture.
    
    :param input_shape: Shape of input tensor (8, 8, 18)
    :param num_filters: Number of convolutional filters  
    :param num_residual_blocks: Number of residual blocks
    :return: Keras model with single value output
    """
    
    common_input = layers.Input(shape=input_shape, name='board_input')
    
    x = layers.Conv2D(num_filters, 
                     kernel_size=(3, 3), 
                     padding='same', 
                     use_bias=False,
                     kernel_regularizer=regularizers.l2(L2_CONST))(common_input)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    
    for _ in range(num_residual_blocks):
        x = build_res_block(x, num_filters)
    
    x = layers.Conv2D(num_filters // 2, 
                     kernel_size=(3, 3), 
                     padding='same', 
                     activation='relu')(x)
    
    body_output = x 
    
    vh = layers.Conv2D(filters=1, 
                      kernel_size=(1, 1), 
                      padding='same', 
                      use_bias=False, 
                      kernel_regularizer=regularizers.l2(L2_CONST))(body_output)
    vh = layers.BatchNormalization()(vh)
    vh = layers.ReLU()(vh)
    vh = layers.Flatten()(vh)
    vh = layers.Dense(128, 
                      activation='relu', 
                      kernel_regularizer=regularizers.l2(L2_CONST))(vh)
    value_output = layers.Dense(1, 
                              activation='linear', # Outputs material value in pawn units (e.g., +3.5 = 3.5 pawn advantage)
                              name='value_output')(vh)

    model = models.Model(
        inputs=common_input,
        outputs=value_output
    )
    
    return model


class OurModel:
    """
    Value-only neural network for chess position evaluation.
    """
    
    def __init__(self):
        """Initialize the value-only model for ML + Minimax architecture"""
        self.model = build_chess_model()
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(
                learning_rate=LEARNING_RATE,
                clipnorm=1.0
            ),
            loss='mean_squared_error',
            metrics=['mae']
        )

    def train(self, path):
        """
        Train the value-only model on position evaluation data.
        
        :param path: Path to training data (CSV or JSONL format)
        """
        x_boards, y_values = self.preprocess_data(path)
        
        print(f"Training value-only model on {len(x_boards)} positions...")
        print(f"Value range: [{y_values.min():.3f}, {y_values.max():.3f}]")
        
        self.model.fit(
            x_boards, 
            y_values,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_split=0.2,
            verbose=1
        )

    def predict(self, fen=None, board_tensor=None):
        """
        Predict position value for a given position.
        
        :param fen: FEN string (optional if board_tensor provided)
        :param board_tensor: Pre-computed tensor (optional if fen provided)
        :return: Single float value in range [-1, 1]
        """
        if board_tensor is None:
            if fen is None:
                raise ValueError("Either 'fen' or 'board_tensor' must be provided")
            converter = TensorConverter()
            board_tensor = converter.convert_for_prediction(fen)

        value_pred = self.model.predict(board_tensor, verbose=0)
        return float(value_pred[0][0])

    def save(self, path):
        """Save the model"""
        self.model.save(path)

    def load(self, path):
        """Load the model"""
        self.model = tf.keras.models.load_model(path)

    def get_architecture(self):
        """Get the model architecture summary"""
        self.model.summary()

    def visualize(self, file_path="DL_Alg/Architecture/model_architecture.png"):
        """
        Visualize the model architecture and save it to a file.
        """
        try:
            tf.keras.utils.plot_model(
                self.model,
                to_file=file_path,
                show_shapes=True,        
                show_layer_names=True,   
                show_dtype=False,
                show_layer_activations=True,
                rankdir='TB'
            )
            print(f"Saved to: {file_path}")
        except ImportError as e:
            print(f"Error details: {e}")

    @staticmethod
    def preprocess_data(path):
        """
        Preprocess training data for value-only model.

        :param path: Path to data file
        :return: Tuple of (x_boards, y_values) - NO policies
        """
        converter = TensorConverter()
        x_boards, y_values = converter.convert(path)  # Value-only conversion
        return x_boards, y_values