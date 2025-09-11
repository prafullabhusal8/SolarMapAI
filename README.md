# 1. create venv
python -m venv venv
venv\Scripts\activate

# 2. install
pip install -r requirements.txt

# 3. preprocess
python src/data_processing.py

# 4. cluster
python src/clustering.py

# 5. optionally generate map standalone
python src/utils.py

# 6. run Streamlit app
streamlit run src/app.py
commands to run python project
