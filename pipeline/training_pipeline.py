from utils.common_functions import read_yaml
from config.paths_config import *
from src.data_ingestion import DataIngestion
from src.data_processing import DataProcessor
from src.model_training import ModelTraining

def run_training_pipeline():
    # 1. Ensure raw data is available
    data_ingestion = DataIngestion(read_yaml(CONFIG_PATH))
    data_ingestion.run()

    # 2. Process data and generate train/test splits + mappings
    data_processor = DataProcessor(ANIMELIST_CSV, PROCESSED_DIR)
    data_processor.run()

    # 3. Train neural recommender and save weights
    model_trainer = ModelTraining(PROCESSED_DIR)
    model_trainer.train_model()

if __name__ == "__main__":
    run_training_pipeline()

