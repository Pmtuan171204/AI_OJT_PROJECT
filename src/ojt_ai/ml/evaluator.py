"""Reserved for out-of-sample evaluation of a trained model."""
def evaluate(*args, **kwargs):
    raise NotImplementedError("ML evaluation requires an implemented trainer, model artifact and independent test labels.")
