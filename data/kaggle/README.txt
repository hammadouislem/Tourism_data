Kaggle data folder
==================

Recommended dataset (large, useful for ML on this project):
  "Hotel Booking Demand" — jessemostipak/hotel-booking-demand
  ~119k hotel bookings with nightly price (adr), length of stay, country, hotel type.

How to get the file here
-------------------------
1) Install: pip install kaggle

2) Authenticate (pick one):

   A) Project .env (recommended for this repo)
      - Copy .env.example to .env in the project root (next to main.py).
      - Fill in:
          KAGGLE_USERNAME=your_kaggle_username
          KAGGLE_KEY=the_long_key_string
        Username and key come from Kaggle -> Settings -> API (same as inside kaggle.json).
      - No spaces around "=".

   B) kaggle.json file
      - Place at: C:\Users\<You>\.kaggle\kaggle.json (from Kaggle -> API -> Create New Token)

3) From the project root you can either:
     python scripts/download_kaggle_hotel_booking.py
   or run the full pipeline — it will download automatically if hotel_booking.csv is missing:
     python main.py

This creates hotel_booking.csv under data/kaggle/ (or a subfolder after unzip).

Optional: limit rows when importing (faster on small PCs)
---------------------------------------------------------
Set environment variable before python main.py:
  Windows PowerShell:  $env:KAGGLE_BOOKING_MAX_ROWS="20000"
  Linux/macOS:         export KAGGLE_BOOKING_MAX_ROWS=20000

Other Kaggle datasets
---------------------
Browse https://www.kaggle.com/datasets and search: hotel, tourism, booking, reviews.
Download any CSV into this folder (or data/external/) and add a mapping in
scraping/source_specs.py using the same keys as booking_export_sample.csv.
