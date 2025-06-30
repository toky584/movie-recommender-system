# 🎬 Personalized Movie Recommender System

A real-time, personalized movie recommender system built with Python and Streamlit. This application demonstrates how to solve the "cold start" problem by allowing a new user to rate movies and instantly receive tailored recommendations based on a pre-trained Alternating Least Squares (ALS) model.

 <!-- Optional: Add a GIF or screenshot of your app! -->

---

## ✨ Features

- **Real-time Personalization:** Get movie recommendations tailored to your taste, even as a brand new user.
- **Interactive Rating:** Rate movies using a simple and intuitive star-rating system.
- **Hybrid Interface:**
    - **Browse & Rate:** Rate movies directly from the recommendation grid.
    - **Search & Rate:** Find any specific movie from a catalog of over 60,000 to add to your ratings.
- **Dynamic UI:** The recommendation grid updates as you provide more ratings, creating an engaging user experience.
- **High-Performance Backend:** The original model was trained using Numba for C-speed calculations.

---

## 📂 Project Structure

This project is organized into several key files:

-   `model_training.ipynb`: A Jupyter Notebook containing all the code for training the Alternating Least Squares (ALS) model from the MovieLens 25M dataset. Running this notebook generates the model files.
-   `process-poster.py`: A Python script that takes the movie data, queries The Movie Database (TMDb) API to fetch poster URLs for each movie, and saves the enriched data.
-   `app.py`: The main Streamlit application file that loads the pre-trained model and serves the interactive user interface.
-   `artifacts/`: This directory stores the output of the model training—the final user/movie vectors and biases.
-   `data/`: This directory stores the raw and processed movie data, including the final `movies_with_posters.csv` used by the app.

---

## ⚙️ How It Works

The project follows a three-step process:

1.  **Train:** The `model_training.ipynb` notebook is run to train the ALS model on the rating data. The resulting vectors and biases are saved as `.npz` and `.pkl` files in the `artifacts/` folder.
2.  **Enrich Data:** The `process-poster.py` script is run to fetch poster images for all movies, creating the `movies_with_posters.csv` file needed by the front-end.
3.  **Serve:** The `app.py` script is launched. It loads the pre-computed artifacts and data to provide a fast, interactive experience for the end-user.

---

## 🛠️ Setup and Installation

To run this application locally, please follow these steps.

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**2. Create a Virtual Environment & Install Dependencies:**
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install required packages
pip install -r requirements.txt
```

**3. Running the Pre-processing Steps (Optional):**
For convenience, the pre-computed artifacts and data are included in this repository. However, you can regenerate them yourself:
   - **Train the Model:** Open and run all cells in the `model_training.ipynb` notebook. This will create the files in the `artifacts/` directory.
   - **Fetch Posters:** In the `process-poster.py` script, add your own TMDb API key. Then run the script from your terminal: `python process-poster.py`. This will create the `movies_with_posters.csv` file.

**4. Download Pre-computed Files with Git LFS:**
If you do not wish to run the pre-processing steps, you can download the existing files using Git LFS.
```bash
# First-time setup for Git LFS
git lfs install

# Download the large model and data files
git lfs pull
```

---

## 🚀 Usage

Once the setup is complete and you have the necessary files in the `artifacts/` and `data/` directories, run the Streamlit app:

```bash
streamlit run app.py
```

A new tab should open in your web browser with the application running.
