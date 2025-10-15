from tflite_runtime.interpreter import Interpreter  # or tflite_flutter if using flutter later

import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_float32.tflite")

interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

def get_interpreter():
    return interpreter
