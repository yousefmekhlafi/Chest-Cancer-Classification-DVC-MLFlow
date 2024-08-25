import tensorflow as tf
from pathlib import Path
import mlflow
import mlflow.keras
from urllib.parse import urlparse
from cnnClassifier.entity.config_entity import EvaluationConfig
from cnnClassifier.utils.common import read_yaml, create_directories, save_json

class Evaluation:
    def __init__(self, config: EvaluationConfig):
        self.config = config

    
    def _valid_generator(self):

        datagenerator_kwargs = dict(
            rescale = 1./255,
            validation_split=0.30
        )

        dataflow_kwargs = dict(
            target_size=self.config.params_image_size[:-1],
            batch_size=self.config.params_batch_size,
            interpolation="bilinear"
        )

        valid_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
            **datagenerator_kwargs
        )

        self.valid_generator = valid_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="validation",
            shuffle=False,
            **dataflow_kwargs
        )


    @staticmethod
    def load_model(path: Path) -> tf.keras.Model:
        return tf.keras.models.load_model(path)
    

    def evaluation(self):
        self.model = self.load_model(self.config.path_of_model)
        self._valid_generator()
        self.score = self.model.evaluate(self.valid_generator)
        self.save_score()

    def save_score(self):
        scores = {"loss": self.score[0], "accuracy": self.score[1]}
        save_json(path=Path("scores.json"), data=scores)

    
def log_into_mlflow(self):
    # Set the MLflow tracking URI
    mlflow.set_tracking_uri('https://dagshub.com/yousefmekhlafi/end-to-end-chest-cancer-classification-mlflow-dvc')
    
    # Set the access token for authentication
    import os
    os.environ['MLFLOW_TRACKING_TOKEN'] = 'd0b4cd5be27b19f397967c9b34dee2aec1d2afb1'

    # Determine the tracking URL type
    tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

    with mlflow.start_run():
        # Log parameters and metrics
        mlflow.log_params(self.config.all_params)
        mlflow.log_metrics(
            {"loss": self.score[0], "accuracy": self.score[1]}
        )
        
        # Register the model if using a supported tracking store
        if tracking_url_type_store != "file":
            mlflow.keras.log_model(self.model, "model", registered_model_name="VGG16Model")
        else:
            mlflow.keras.log_model(self.model, "model")