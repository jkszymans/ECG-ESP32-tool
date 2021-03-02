import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA = os.path.join(BASE_DIR, 'media')

DATA = os.path.join(BASE_DIR, 'data')

print(MEDIA)