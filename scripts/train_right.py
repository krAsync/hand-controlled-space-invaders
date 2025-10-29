import pandas as pd
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import csv
import joblib

df = pd.read_csv('../data/numbers/right.csv')

y = df.iloc[:, 0]
x = df.iloc[:, 1:]

encoder = LabelEncoder

X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
        )

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f'Accuracy for right hand model: {accuracy:.2f}')
joblib.dump(model, '../models/random_forest_right.pkl')
print('Saved right hand model.')
