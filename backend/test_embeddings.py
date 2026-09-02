from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


print("=" * 60)
print("LOADING EMBEDDING MODEL")
print("=" * 60)

model = SentenceTransformer(MODEL_NAME)

print("Model loaded successfully.")
print("Model:", MODEL_NAME)

text = "EX-110 10W aluminium tiltable spotlight"

embedding = model.encode(text)

print("Embedding generated successfully.")
print("Vector dimensions:", len(embedding))
print("First 5 values:", embedding[:5])

print("=" * 60)
print("EMBEDDING TEST PASSED")
print("=" * 60)