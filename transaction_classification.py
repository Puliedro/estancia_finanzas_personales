import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

def classify_transactions(df):
    # Filter the DataFrame for valid descriptions and categories
    df_filtered = df[df['Description'].notnull() & df['Category'].notnull()]

    # Preprocess the text
    df_filtered['Description_clean'] = df_filtered['Description'].str.lower().str.replace('[^a-z ]', '', regex=True)

    # Split the dataset into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(df_filtered['Description_clean'], df_filtered['Category'], test_size=0.2, random_state=42)

    # Initialize the TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

    # Learn the vocabulary and vectorize the training set
    X_train_vectors = vectorizer.fit_transform(X_train)

    # Vectorize the test set
    X_test_vectors = vectorizer.transform(X_test)

    # Initialize the classifier
    model = LogisticRegression(max_iter=1000)

    # Train the model
    model.fit(X_train_vectors, y_train)

    # Predict the categories for the test set
    y_pred = model.predict(X_test_vectors)

    # Display the classification report
    print(classification_report(y_test, y_pred))

    # Display the confusion matrix
    conf_mat = confusion_matrix(y_test, y_pred, labels=model.classes_)
    sns.heatmap(conf_mat, annot=True, fmt="d", cmap="Blues", xticklabels=model.classes_, yticklabels=model.classes_)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.title('Confusion Matrix')
    plt.show()

    ingresos_sum = df['Credit'].dropna().sum()
    gastos_sum = df['Debit'].dropna().sum()

    # Calculate the percentage of income spent
    if ingresos_sum > 0:  # To avoid division by zero
        percent_spent = (gastos_sum / ingresos_sum) * 100
    else:
        percent_spent = 0

    # Print the percentage of income spent
    print(f"Percentage of Income Spent: {percent_spent:.2f}%")

    return model, vectorizer, percent_spent
