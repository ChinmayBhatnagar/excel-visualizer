from flask import Flask, request, render_template
import pandas as pd
import plotly.express as px
import os
import werkzeug

# Initialize Flask app
app = Flask(__name__)

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            # Secure filename to prevent directory traversal attacks
            filename = werkzeug.utils.secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Read file (Excel or CSV)
            try:
                if filename.endswith(".xlsx"):
                    df = pd.read_excel(file_path, engine='openpyxl')
                elif filename.endswith(".xls"):
                    df = pd.read_excel(file_path, engine='xlrd')
                elif filename.endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    return "Unsupported file format! Please upload an Excel (.xlsx, .xls) or CSV file."
            except Exception as e:
                return f"Error reading file: {str(e)}"

            # Convert DataFrame to HTML for display
            table_html = df.head().to_html(classes="table table-striped", index=False)

            # Get all columns (both numeric and non-numeric)
            all_columns = df.columns.tolist()

            # Separate numeric columns
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

            return render_template("index.html", table_html=table_html, columns=all_columns, numeric_columns=numeric_columns, filename=filename)

    return render_template("index.html", table_html=None, columns=[], numeric_columns=[])

@app.route("/visualize", methods=["POST"])
def visualize():
    column = request.form.get("column", "").strip()  # Remove leading/trailing spaces
    file_name = request.form.get("filename", "").strip()

    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    try:
        if file_name.endswith(".xlsx"):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_name.endswith(".xls"):
            df = pd.read_excel(file_path, engine='xlrd')
        elif file_name.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            return "Invalid file format!"
    except Exception as e:
        return f"Error reading file: {str(e)}"

    # Normalize column names for case-insensitive matching
    df.columns = df.columns.str.strip()
    if column not in df.columns:
        # Ensure column names are converted to strings before using join
        column_names = [str(col) for col in df.columns]
        return f"Invalid column selected! Available: {', '.join(column_names)}"

    # Visualization options
    visualization_type = request.form.get("visualization_type", "histogram")

    # Check if the selected column is numeric for histogram and box plot
    if visualization_type in ["histogram", "box"] and column not in df.select_dtypes(include=['number']).columns:
        return f"Error: The selected column '{column}' is not numeric and cannot be used for a {visualization_type}."

    # Generate interactive graph based on selected visualization type
    if visualization_type == "pie":
        fig = px.pie(df, names=column, title=f"Distribution of {column}")
    elif visualization_type == "box":
        fig = px.box(df, y=column, title=f"Box Plot of {column}")
    else:
        fig = px.histogram(df, x=column, title=f"Distribution of {column}", nbins=30)

    graph_html = fig.to_html(full_html=False)

    return render_template("index.html", table_html=df.head().to_html(classes="table table-striped", index=False),
                           columns=df.columns.tolist(),
                           numeric_columns=df.select_dtypes(include=['number']).columns.tolist(),
                           filename=file_name, graph_html=graph_html)

if __name__ == "__main__":
    app.run(debug=True)
