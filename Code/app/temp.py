from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.neighbors import NearestNeighbors

def train_content_based_model(df):
    # Encode categorical variables
    label_encoders = {}
    for col in ['Branch_Code', 'Location']:
        label_encoders[col] = LabelEncoder()
        # label_encoders[col] = LabelEncoder(handle_unknown='ignore')

        df[col] = label_encoders[col].fit_transform(df[col])

    # Convert text data into numerical vectors
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['College_Name'])

    # Combine numerical features with text features
    X = df[['Branch_Code', 'Location']]
    X_sparse = sparse.hstack([tfidf_matrix, X])

    # Train nearest neighbors model
    k = 5  # Number of nearest neighbors to consider
    model = NearestNeighbors(n_neighbors=k, algorithm='brute', metric='cosine')
    model.fit(X_sparse)
    
    return model, label_encoders


def recommend_colleges(model, label_encoders, cutoff, branch, location, community, df, k=50):
    # Encode user preferences
    branch_encoded = label_encoders['Branch_Code'].transform([branch])[0]
    # community_encoded = label_encoders[community].transform([community])[0]
    location_encoded = label_encoders['Location'].transform([location])[0]

    # Filter colleges based on user preferences
    filtered_df = df[(df[community] <= float(cutoff)) & 
                     (df['Branch_Code'] == branch_encoded) &
                     (df['Location'] == location_encoded)
                    ]

    college_avg_cutoffs = filtered_df.groupby('College_Name')[community].mean()

    # Sort colleges based on average cutoff and select top k
    recommended_colleges = college_avg_cutoffs.sort_values().head(k).index.tolist()
    return recommended_colleges