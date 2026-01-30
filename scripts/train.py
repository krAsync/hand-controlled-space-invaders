import pandas as pd
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
from pathlib import Path 

script_path = Path(__file__).resolve()
root_dir = script_path.parent.parent
data_path = root_dir/'data'/'retro'/'gestures.csv'
model_path = root_dir/'models'/'rf_model.pkl'
df = pd.read_csv(data_path, header=None)
if len(df) < 2:
    print("Not enough data to train the model. Please capture more gestures.")
else:
    y = df.iloc[1:, 0]

    # Encode handedness (column 1)
    handedness = df.iloc[1:, 1].astype('category').cat.codes

    # Landmark data starts from column 2
    landmarks = df.iloc[1:, 2:]

    # Combine handedness and landmarks into features
    X = pd.concat([handedness, landmarks], axis=1)

    X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
            )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f'Accuracy for unified model: {accuracy:.2f}')
    joblib.dump(model, model_path)
    print('Saved unified gesture model.')
