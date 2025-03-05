import streamlit as st
import base64
import os

def get_base64_encoded_image(image_path):
    """Get base64 encoded version of an image"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def load_css():
    """Load custom CSS to style the application"""
    st.markdown("""
        <style>
        /* Main styling */
        .header-container {
            padding: 1rem 0;
            margin-bottom: 2rem;
            text-align: center;
            background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
        }
        .header-container h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: #172b4d;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #42526e;
            font-weight: 300;
        }

        /* Input field styling with light blue background */
        .stTextInput > div > div > input, 
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            background-color: rgba(200, 230, 255, 0.2) !important;
            transition: background-color 0.3s, border 0.3s !important;
        }

        .stTextInput > div > div > input:focus, 
        .stNumberInput > div > div > input:focus,
        .stDateInput > div > div > input:focus {
            background-color: rgba(200, 230, 255, 0.4) !important;
            border: 1px solid #4a90e2 !important;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
        }

        /* Make sure the multiselect fields also have the styling */
        .stMultiSelect div[data-baseweb="select"] {
            background-color: rgba(200, 230, 255, 0.2) !important;
        }

        .stMultiSelect div[data-baseweb="select"]:focus-within {
            background-color: rgba(200, 230, 255, 0.4) !important;
            border: 1px solid #4a90e2 !important;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
        }

        /* Styling for select boxes */
        .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(200, 230, 255, 0.2) !important;
        }

        .stSelectbox div[data-baseweb="select"]:focus-within {
            background-color: rgba(200, 230, 255, 0.4) !important;
            border: 1px solid #4a90e2 !important;
        }

        /* Additional styling for other form elements */
        input[type="text"], input[type="number"], input[type="date"], select, textarea {
            border: 1px solid #dfe1e6;
            border-radius: 3px;
            padding: 8px 10px;
            width: 100%;
            box-sizing: border-box;
            background-color: rgba(200, 230, 255, 0.2);
        }

        input[type="text"]:focus, input[type="number"]:focus, input[type="date"]:focus, select:focus, textarea:focus {
            border-color: #4c9aff;
            background-color: rgba(200, 230, 255, 0.4);
            outline: none;
            box-shadow: 0 0 0 2px rgba(76, 154, 255, 0.3);
        }

        /* Button styling */
        .stButton>button {
            background-color: #0052cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 3px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .stButton>button:hover {
            background-color: #0747a6;
        }

        /* Data editor styling */
        .stDataEditor {
            font-family: 'Inter', sans-serif;
        }

        .stDataEditor td:not([disabled="true"]) {
            background-color: rgba(200, 230, 255, 0.2) !important;
        }

        .stDataEditor td:not([disabled="true"]):hover {
            background-color: rgba(200, 230, 255, 0.4) !important;
            border: 1px solid #2196F3 !important;
        }
        </style>
    """, unsafe_allow_html=True)