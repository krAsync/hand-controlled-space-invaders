import pandas as pd
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import csv
import joblib

df = pd.read_csv('../data/numbers/left.csv')

y = df.iloc[:, 0]
x = df.iloc[:, 1:]

encoder = LabelEncoder
print(y[40:150])

X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
        )

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f'ACC {accuracy:.2f}')
if input(f'would you like to save model? (Y/N)').lower() ==  'y':
    joblib.dump(model, '../models/random_forest01.pkl')
else:
    print('exiting')

